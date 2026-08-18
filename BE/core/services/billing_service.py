"""Billing helpers: plan resolution, keyword limits, subscription sync."""

from __future__ import annotations

import logging
from typing import Any

from core.models import Keyword, UserProfile
from core.plans import (
    ACTIVE_SUBSCRIPTION_STATUSES,
    PLAN_BUSINESS,
    PLAN_FREE,
    PLAN_PRO,
    PLATFORM_LABELS,
    is_paid_plan,
    known_product_ids,
    limits_for_plan,
    normalize_checkout_plan,
    plan_for_product_id,
    plan_rank,
    product_id_for_plan,
)

logger = logging.getLogger(__name__)

METERED_PLATFORMS = ("reddit", "hackernews", "twitter", "youtube")


def get_or_create_profile(user_id: str) -> UserProfile:
    profile = UserProfile.objects(user_id=user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        profile.save()
    return profile


def resolve_plan(profile: UserProfile) -> str:
    """
    Paid plans stay active while Dodo status is active — including cancel_at_period_end.
    Access ends only after status leaves the active set (cancelled/expired/etc.).
    """
    status = (profile.subscription_status or "").lower()
    if is_paid_plan(profile.plan) and status in ACTIVE_SUBSCRIPTION_STATUSES:
        return profile.plan
    # Legacy / webhook race: subscription id present and active status
    if status in ACTIVE_SUBSCRIPTION_STATUSES and profile.dodo_subscription_id:
        mapped = plan_for_product_id(getattr(profile, "dodo_product_id", None))
        if mapped:
            return mapped
        if is_paid_plan(profile.plan):
            return profile.plan
        return PLAN_PRO
    return PLAN_FREE


def _format_billing_date(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    text = str(value).strip()
    return text or None


def billing_status_payload(user_id: str) -> dict[str, Any]:
    profile = get_or_create_profile(user_id)
    plan = resolve_plan(profile)
    limits = limits_for_plan(plan)
    usage = keyword_usage(user_id, active_only=True)
    total_usage = keyword_usage(user_id, active_only=False)
    remaining = {
        p: max(0, limits.get(p, 0) - usage.get(p, 0)) for p in METERED_PLATFORMS
    }
    cancel_at_period_end = bool(profile.cancel_at_period_end) and is_paid_plan(plan)

    # Auto-pause if somehow still actively over current plan caps.
    if _has_over_limit_active(usage, limits):
        enforce_downgrade_keyword_limits(user_id)
        profile.reload()
        usage = keyword_usage(user_id, active_only=True)
        total_usage = keyword_usage(user_id, active_only=False)
        remaining = {
            p: max(0, limits.get(p, 0) - usage.get(p, 0)) for p in METERED_PLATFORMS
        }
        plan = resolve_plan(profile)

    return {
        "plan": plan,
        "subscriptionStatus": profile.subscription_status,
        "dodoCustomerId": profile.dodo_customer_id,
        "dodoSubscriptionId": profile.dodo_subscription_id,
        "dodoProductId": getattr(profile, "dodo_product_id", None),
        "cancelAtPeriodEnd": cancel_at_period_end,
        "nextBillingDate": profile.next_billing_date,
        "needsKeywordSelection": bool(profile.needs_keyword_selection),
        "limits": limits,
        "usage": usage,
        "totalUsage": total_usage,
        "remaining": remaining,
        "canUpgrade": plan != PLAN_BUSINESS,
        "canUpgradePro": plan == PLAN_FREE,
        "canUpgradeBusiness": plan in (PLAN_FREE, PLAN_PRO),
        "canReactivate": cancel_at_period_end and bool(profile.dodo_subscription_id),
        "canManageBilling": bool(profile.dodo_customer_id),
    }


def keyword_usage(user_id: str, *, active_only: bool = True) -> dict[str, int]:
    usage = {p: 0 for p in METERED_PLATFORMS}
    for platform in METERED_PLATFORMS:
        query: dict[str, Any] = {
            "user_id": user_id,
            "platform__in": [platform, "all"],
        }
        if active_only:
            query["is_active"] = True
        usage[platform] = Keyword.objects(**query).count()
    return usage


def _has_over_limit_active(
    usage: dict[str, int], limits: dict[str, int]
) -> bool:
    for platform in METERED_PLATFORMS:
        limit = limits.get(platform, 0)
        used = usage.get(platform, 0)
        if used > limit:
            return True
    return False


def check_can_add_keyword(user_id: str, platform: str) -> tuple[bool, str | None]:
    """Return (ok, error_message). platform may be a single platform or 'all'."""
    ok, err, _ = check_can_add_keywords(user_id, [platform])
    return ok, err


def check_can_add_keywords(
    user_id: str, platforms: list[str]
) -> tuple[bool, str | None, str | None]:
    """
    Hard-check plan limits for one or more platforms in a single create.

    Counts projected usage so multi-create cannot exceed the cap.
    Returns (ok, error_message, platform_or_none).
    """
    profile = get_or_create_profile(user_id)
    plan = resolve_plan(profile)
    limits = limits_for_plan(plan)
    usage = keyword_usage(user_id, active_only=True)
    projected = dict(usage)

    expanded: list[str] = []
    for platform in platforms:
        if platform == "all":
            expanded.extend(METERED_PLATFORMS)
        else:
            expanded.append(platform)

    for p in expanded:
        if p not in limits:
            continue
        limit = limits[p]
        label = PLATFORM_LABELS.get(p, p)
        if limit <= 0:
            if plan == PLAN_FREE:
                return (
                    False,
                    f"{label} monitoring requires Pro. Upgrade to add {label} keywords.",
                    p,
                )
            return False, f"{label} keywords are not available on your plan.", p
        if projected[p] >= limit:
            return (
                False,
                (
                    f"You've reached the {label} keyword limit ({limit}) on the "
                    f"{plan.capitalize()} plan. Upgrade or remove a keyword to continue."
                ),
                p,
            )
        projected[p] += 1
    return True, None, None


def _attr(obj: Any, *names: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        for name in names:
            if name in obj and obj[name] is not None:
                return obj[name]
        return None
    for name in names:
        value = getattr(obj, name, None)
        if value is not None:
            return value
    return None


def _metadata_dict(raw: Any) -> dict[str, str]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items() if v is not None}
    if hasattr(raw, "model_dump"):
        dumped = raw.model_dump()
        if isinstance(dumped, dict):
            return {str(k): str(v) for k, v in dumped.items() if v is not None}
    return {}


def _customer_id(subscription: Any) -> str | None:
    customer = _attr(subscription, "customer")
    if customer is None:
        return None
    if isinstance(customer, dict):
        return customer.get("customer_id") or customer.get("customerId")
    return getattr(customer, "customer_id", None)


def _normalize_status(status: Any) -> str | None:
    if status is None:
        return None
    if isinstance(status, str):
        return status.lower()
    # Enum-like objects
    value = getattr(status, "value", None)
    if isinstance(value, str):
        return value.lower()
    return str(status).lower()


def apply_subscription_to_profile(
    profile: UserProfile,
    subscription: Any,
) -> UserProfile:
    """Write subscription fields onto an existing profile and persist."""
    previous_plan = resolve_plan(profile)
    customer_id = _customer_id(subscription)
    subscription_id = _attr(subscription, "subscription_id", "subscriptionId")
    product_id = _attr(subscription, "product_id", "productId")
    status = _normalize_status(_attr(subscription, "status"))
    cancel_flag = _attr(
        subscription,
        "cancel_at_next_billing_date",
        "cancelAtNextBillingDate",
    )
    next_billing = _format_billing_date(
        _attr(subscription, "next_billing_date", "nextBillingDate")
    )

    if customer_id:
        profile.dodo_customer_id = customer_id
    if subscription_id:
        profile.dodo_subscription_id = subscription_id
    if product_id:
        profile.dodo_product_id = product_id
    if status:
        profile.subscription_status = status

    mapped_plan = plan_for_product_id(product_id)

    if status in ACTIVE_SUBSCRIPTION_STATUSES:
        profile.plan = mapped_plan or (
            profile.plan if is_paid_plan(profile.plan) else PLAN_PRO
        )
        profile.cancel_at_period_end = bool(cancel_flag)
        if next_billing:
            profile.next_billing_date = next_billing
        # Upgrading / staying paid clears the Free pick-flow requirement.
        profile.needs_keyword_selection = False
    else:
        # cancelled / on_hold / expired / failed / paused → free access
        profile.plan = PLAN_FREE
        profile.cancel_at_period_end = False
        if next_billing:
            profile.next_billing_date = next_billing

    profile.save()
    logger.info(
        "Synced billing for user %s → plan=%s status=%s cancel_at_period_end=%s sub=%s product=%s",
        profile.user_id,
        profile.plan,
        profile.subscription_status,
        profile.cancel_at_period_end,
        profile.dodo_subscription_id,
        getattr(profile, "dodo_product_id", None),
    )

    new_plan = resolve_plan(profile)
    if plan_rank(previous_plan) > plan_rank(new_plan):
        enforce_downgrade_keyword_limits(profile.user_id)
    elif new_plan == PLAN_FREE:
        # Catch Free users who drifted over-limit without a paid→Free transition.
        maybe_flag_over_limit_selection(profile.user_id)

    return profile


def enforce_downgrade_keyword_limits(user_id: str) -> None:
    """
    After a plan drop: pause keywords that don't fit the new caps and require a pick.

    - Platforms with limit 0: deactivate all.
    - Platforms over the active cap: deactivate all on that platform so the
      user must choose which ones to keep.
    """
    profile = get_or_create_profile(user_id)
    plan = resolve_plan(profile)
    limits = limits_for_plan(plan)
    needs_selection = False

    for platform in METERED_PLATFORMS:
        limit = limits.get(platform, 0)
        keywords = list(
            Keyword.objects(
                user_id=user_id,
                platform__in=[platform, "all"],
            ).order_by("-created_at")
        )
        active = [k for k in keywords if k.is_active]

        if limit <= 0:
            for kw in active:
                kw.is_active = False
                kw.save()
            continue

        if len(active) > limit:
            needs_selection = True
            for kw in active:
                kw.is_active = False
                kw.save()

    profile.needs_keyword_selection = needs_selection
    profile.save()
    logger.info(
        "Downgrade enforce for %s: needs_keyword_selection=%s",
        user_id,
        needs_selection,
    )


def maybe_flag_over_limit_selection(user_id: str) -> None:
    """If active keywords already exceed plan limits, require selection."""
    profile = get_or_create_profile(user_id)
    plan = resolve_plan(profile)
    limits = limits_for_plan(plan)
    usage = keyword_usage(user_id, active_only=True)
    if _has_over_limit_active(usage, limits):
        enforce_downgrade_keyword_limits(user_id)


def keyword_selection_payload(user_id: str) -> dict[str, Any]:
    """Candidates + limits for the pick-which-to-keep UI."""
    profile = get_or_create_profile(user_id)
    plan = resolve_plan(profile)
    limits = limits_for_plan(plan)
    platforms_out: list[dict[str, Any]] = []

    for platform in METERED_PLATFORMS:
        limit = limits.get(platform, 0)
        keywords = list(
            Keyword.objects(
                user_id=user_id,
                platform__in=[platform, "all"],
            ).order_by("-created_at")
        )
        if not keywords and limit > 0:
            continue
        # Always include platforms that have keywords or require a choice.
        if not keywords and limit <= 0:
            continue
        platforms_out.append(
            {
                "platform": platform,
                "label": PLATFORM_LABELS.get(platform, platform),
                "limit": limit,
                "requiresSelection": limit > 0 and len(keywords) > limit,
                "locked": limit <= 0,
                "keywords": [
                    {
                        "id": str(k.id),
                        "keyword": k.keyword,
                        "platform": k.platform,
                        "enabled": bool(k.is_active),
                        "createdAt": k.created_at.isoformat() if k.created_at else None,
                    }
                    for k in keywords
                ],
            }
        )

    return {
        "plan": plan,
        "needsKeywordSelection": bool(profile.needs_keyword_selection),
        "platforms": platforms_out,
        "limits": limits,
    }


def apply_keyword_selection(
    user_id: str, keep_ids: list[str]
) -> dict[str, Any]:
    """
    Activate the chosen keywords (within plan caps) and pause the rest.

    keep_ids: flat list of keyword document ids the user wants to keep active.
    """
    profile = get_or_create_profile(user_id)
    plan = resolve_plan(profile)
    limits = limits_for_plan(plan)
    keep_set = {str(x) for x in keep_ids}

    # Validate ownership and group by platform.
    owned = {
        str(k.id): k
        for k in Keyword.objects(user_id=user_id, id__in=list(keep_set))
    }
    unknown = keep_set - set(owned.keys())
    if unknown:
        raise ValueError("One or more keywords were not found on your account.")

    by_platform: dict[str, list[Keyword]] = {p: [] for p in METERED_PLATFORMS}
    for kw in owned.values():
        platform = kw.platform if kw.platform != "all" else "reddit"
        if platform not in by_platform:
            raise ValueError(f"Unsupported platform: {platform}")
        by_platform[platform].append(kw)

    for platform, selected in by_platform.items():
        limit = limits.get(platform, 0)
        if len(selected) > limit:
            label = PLATFORM_LABELS.get(platform, platform)
            raise ValueError(
                f"You can keep at most {limit} {label} keyword(s) on the "
                f"{plan.capitalize()} plan."
            )
        if limit <= 0 and selected:
            label = PLATFORM_LABELS.get(platform, platform)
            raise ValueError(
                f"{label} keywords are not available on the {plan.capitalize()} plan."
            )

    # Apply per platform:
    # - limit 0: deactivate all
    # - over Free cap: activate only keep_ids
    # - under/at cap with no keep_ids for that platform: leave alone
    # - under/at cap with keep_ids: honor the selection
    for platform in METERED_PLATFORMS:
        limit = limits.get(platform, 0)
        keywords = list(
            Keyword.objects(user_id=user_id, platform__in=[platform, "all"])
        )
        selected_ids = {str(k.id) for k in by_platform.get(platform, [])}

        if limit <= 0:
            for kw in keywords:
                if kw.is_active:
                    kw.is_active = False
                    kw.save()
            continue

        over_cap = len(keywords) > limit
        if not over_cap and not selected_ids:
            continue

        for kw in keywords:
            should_active = str(kw.id) in selected_ids
            if kw.is_active != should_active:
                kw.is_active = should_active
                kw.save()

    profile.needs_keyword_selection = False
    profile.save()
    return billing_status_payload(user_id)


def check_can_activate_keyword(user_id: str, keyword: Keyword) -> tuple[bool, str | None]:
    """Guard re-enabling a paused keyword against plan active caps."""
    if keyword.is_active:
        return True, None
    platform = keyword.platform if keyword.platform != "all" else "reddit"
    return check_can_add_keyword(user_id, platform)


def reactivate_plan(user_id: str) -> dict[str, Any]:
    """
    Clear cancel_at_next_billing_date on the user's active paid subscription.
    Prefer this over creating a second checkout while still in the paid period.
    """
    from core.services import dodo_service

    profile = get_or_create_profile(user_id)
    current = resolve_plan(profile)
    if not is_paid_plan(current):
        raise ValueError("No active paid subscription to reactivate.")
    if not profile.cancel_at_period_end:
        return billing_status_payload(user_id)
    if not profile.dodo_subscription_id:
        raise ValueError("Missing subscription id; open Manage billing to continue.")

    updated = dodo_service.reactivate_subscription(profile.dodo_subscription_id)
    apply_subscription_to_profile(profile, updated)
    profile.reload()
    return billing_status_payload(user_id)


def start_plan_checkout(
    user_id: str,
    *,
    plan: str,
    email: str,
    name: str | None,
    return_url: str,
    cancel_url: str,
) -> dict[str, Any]:
    """
    Start checkout for Free→paid, reactivate a scheduled cancel on the same plan,
    or change_plan when upgrading Pro→Business on an existing subscription.
    """
    from core.services import dodo_service

    target = normalize_checkout_plan(plan)
    product_id = product_id_for_plan(target)
    profile = get_or_create_profile(user_id)
    current = resolve_plan(profile)

    if current == target:
        if profile.cancel_at_period_end and profile.dodo_subscription_id:
            payload = reactivate_plan(user_id)
            return {"reactivated": True, **payload}
        raise ValueError(f"You are already on the {target.capitalize()} plan.")

    # Paid → higher paid: change existing subscription instead of a second checkout.
    if is_paid_plan(current) and plan_rank(target) > plan_rank(current):
        if not profile.dodo_subscription_id:
            raise ValueError("Missing subscription id; open Manage billing to continue.")
        if profile.cancel_at_period_end:
            # Undo cancel first so the upgrade applies to a renewing sub.
            dodo_service.reactivate_subscription(profile.dodo_subscription_id)
        updated = dodo_service.change_subscription_plan(
            profile.dodo_subscription_id,
            product_id=product_id,
            proration_billing_mode="prorated_immediately",
        )
        apply_subscription_to_profile(profile, updated)
        profile.reload()
        return {"changedPlan": True, **billing_status_payload(user_id)}

    if is_paid_plan(current) and plan_rank(target) < plan_rank(current):
        raise ValueError(
            "To move to a lower plan, use Manage billing in the customer portal."
        )

    result = dodo_service.create_checkout(
        product_id=product_id,
        customer_email=email,
        customer_name=name,
        clerk_user_id=user_id,
        dodo_customer_id=profile.dodo_customer_id or None,
        return_url=return_url,
        cancel_url=cancel_url,
    )
    if result.get("customerId"):
        profile.dodo_customer_id = result["customerId"]
        profile.save()
    return result


def _resolve_user_id_from_subscription(subscription: Any) -> str | None:
    metadata = _metadata_dict(_attr(subscription, "metadata"))
    user_id = metadata.get("clerk_user_id") or metadata.get("user_id")
    if user_id:
        return user_id

    customer_id = _customer_id(subscription)
    if not customer_id:
        return None

    profile = UserProfile.objects(dodo_customer_id=customer_id).first()
    if profile:
        return profile.user_id

    # Fall back to Dodo customer metadata (set when we create the customer).
    try:
        from core.services import dodo_service

        customer = dodo_service.retrieve_customer(customer_id)
        customer_meta = _metadata_dict(_attr(customer, "metadata"))
        return customer_meta.get("clerk_user_id") or customer_meta.get("user_id")
    except Exception:
        logger.exception(
            "Failed to resolve clerk user from Dodo customer %s", customer_id
        )
        return None


def apply_subscription_event(subscription: Any) -> UserProfile | None:
    """Sync UserProfile from a Dodo subscription object (webhook or API)."""
    subscription_id = _attr(subscription, "subscription_id", "subscriptionId")
    customer_id = _customer_id(subscription)
    metadata = _metadata_dict(_attr(subscription, "metadata"))

    user_id = _resolve_user_id_from_subscription(subscription)
    profile = None
    if user_id:
        profile = get_or_create_profile(user_id)
    elif subscription_id:
        profile = UserProfile.objects(dodo_subscription_id=subscription_id).first()
    elif customer_id:
        profile = UserProfile.objects(dodo_customer_id=customer_id).first()

    if not profile:
        logger.warning(
            "Dodo subscription event with no matching user (sub=%s customer=%s meta=%s)",
            subscription_id,
            customer_id,
            metadata,
        )
        return None

    return apply_subscription_to_profile(profile, subscription)


def apply_payment_event(payment: Any) -> UserProfile | None:
    """
    Handle payment webhooks. If the payment is tied to a subscription and succeeded,
    pull the subscription and sync the matching user.
    """
    status = _normalize_status(_attr(payment, "status"))
    succeeded = status in {"succeeded", "paid", "complete", "completed"}
    subscription_id = _attr(payment, "subscription_id", "subscriptionId")
    metadata = _metadata_dict(_attr(payment, "metadata"))
    user_id = metadata.get("clerk_user_id") or metadata.get("user_id")
    customer_id = _customer_id(payment)

    if not succeeded:
        logger.info("Ignoring non-succeeded payment status=%s", status)
        return None

    if subscription_id:
        try:
            from core.services import dodo_service

            subscription = dodo_service.retrieve_subscription(subscription_id)
            if user_id:
                profile = get_or_create_profile(user_id)
                if customer_id:
                    profile.dodo_customer_id = customer_id
                return apply_subscription_to_profile(profile, subscription)
            return apply_subscription_event(subscription)
        except Exception:
            logger.exception(
                "Failed to sync subscription %s from payment event", subscription_id
            )

    # Payment without subscription_id — still attach customer for later sync.
    if user_id and customer_id:
        profile = get_or_create_profile(user_id)
        profile.dodo_customer_id = customer_id
        profile.save()
        return profile
    return None


def sync_plan_from_dodo(user_id: str, *, email: str | None = None) -> dict[str, Any]:
    """
    Pull the latest subscription state from Dodo for this user and update the profile.

    Called on return from checkout so plan activation does not depend solely on webhooks.
    """
    from core.services import dodo_service

    profile = get_or_create_profile(user_id)
    customer_id = profile.dodo_customer_id or None
    product_ids = known_product_ids()

    if not customer_id and email:
        customer_id = dodo_service.ensure_customer(
            email=email,
            name=None,
            clerk_user_id=user_id,
            existing_customer_id=None,
        )
        if customer_id:
            profile.dodo_customer_id = customer_id
            profile.save()

    if not customer_id:
        logger.warning("Cannot sync billing for %s: no Dodo customer id", user_id)
        return billing_status_payload(user_id)

    # Prefer an existing subscription id, then active/pending across known products.
    candidates: list[Any] = []
    if profile.dodo_subscription_id:
        try:
            candidates.append(
                dodo_service.retrieve_subscription(profile.dodo_subscription_id)
            )
        except Exception:
            logger.info(
                "Stored subscription %s not retrievable; listing by customer",
                profile.dodo_subscription_id,
                exc_info=True,
            )

    def _list_for(*, status: str | None = None, product_id: str | None = None) -> None:
        try:
            found = dodo_service.list_subscriptions_for_customer(
                customer_id,
                status=status,
                product_id=product_id,
            )
            candidates.extend(found)
        except Exception:
            logger.exception(
                "Failed listing subscriptions for customer %s status=%s product=%s",
                customer_id,
                status,
                product_id,
            )

    for status in ("active", "pending"):
        if product_ids:
            for pid in product_ids:
                _list_for(status=status, product_id=pid)
        else:
            _list_for(status=status)

    if not candidates:
        if product_ids:
            for pid in product_ids:
                _list_for(product_id=pid)
        else:
            _list_for()

    # Deduplicate by subscription_id, prefer active + higher plan.
    by_id: dict[str, Any] = {}
    for sub in candidates:
        sid = _attr(sub, "subscription_id", "subscriptionId")
        if not sid:
            continue
        existing = by_id.get(sid)
        if existing is None:
            by_id[sid] = sub
            continue
        existing_status = _normalize_status(_attr(existing, "status"))
        new_status = _normalize_status(_attr(sub, "status"))
        if new_status == "active" and existing_status != "active":
            by_id[sid] = sub

    if not by_id:
        logger.info(
            "No Dodo subscriptions found for user %s customer %s",
            user_id,
            customer_id,
        )
        return billing_status_payload(user_id)

    def sort_key(sub: Any) -> tuple[int, int, str]:
        status = _normalize_status(_attr(sub, "status")) or ""
        status_rank = 0 if status == "active" else 1 if status == "pending" else 2
        product_id = _attr(sub, "product_id", "productId")
        mapped = plan_for_product_id(product_id) or PLAN_FREE
        # Higher plan first within same status (negate rank).
        return (
            status_rank,
            -plan_rank(mapped),
            _attr(sub, "subscription_id", "subscriptionId") or "",
        )

    best = sorted(by_id.values(), key=sort_key)[0]
    apply_subscription_to_profile(profile, best)
    profile.reload()
    return billing_status_payload(user_id)
