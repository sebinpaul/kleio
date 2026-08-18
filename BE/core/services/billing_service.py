"""Billing helpers: plan resolution, keyword limits, subscription sync."""

from __future__ import annotations

import logging
from typing import Any

from core.models import Keyword, UserProfile
from core.plans import (
    ACTIVE_SUBSCRIPTION_STATUSES,
    PLAN_FREE,
    PLAN_PRO,
    PLATFORM_LABELS,
    limits_for_plan,
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
    status = (profile.subscription_status or "").lower()
    if profile.plan == PLAN_PRO and status in ACTIVE_SUBSCRIPTION_STATUSES:
        return PLAN_PRO
    # Legacy / webhook race: subscription id present and active status
    if status in ACTIVE_SUBSCRIPTION_STATUSES and profile.dodo_subscription_id:
        return PLAN_PRO
    return PLAN_FREE


def keyword_usage(user_id: str) -> dict[str, int]:
    usage = {p: 0 for p in METERED_PLATFORMS}
    for platform in METERED_PLATFORMS:
        usage[platform] = Keyword.objects(
            user_id=user_id,
            platform__in=[platform, "all"],
        ).count()
    return usage


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
    usage = keyword_usage(user_id)
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


def billing_status_payload(user_id: str) -> dict[str, Any]:
    profile = get_or_create_profile(user_id)
    plan = resolve_plan(profile)
    limits = limits_for_plan(plan)
    usage = keyword_usage(user_id)
    remaining = {
        p: max(0, limits.get(p, 0) - usage.get(p, 0)) for p in METERED_PLATFORMS
    }
    return {
        "plan": plan,
        "subscriptionStatus": profile.subscription_status,
        "dodoCustomerId": profile.dodo_customer_id,
        "dodoSubscriptionId": profile.dodo_subscription_id,
        "limits": limits,
        "usage": usage,
        "remaining": remaining,
        "canUpgrade": plan != PLAN_PRO,
        "canManageBilling": bool(profile.dodo_customer_id),
    }


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
    customer_id = _customer_id(subscription)
    subscription_id = _attr(subscription, "subscription_id", "subscriptionId")
    status = _normalize_status(_attr(subscription, "status"))

    if customer_id:
        profile.dodo_customer_id = customer_id
    if subscription_id:
        profile.dodo_subscription_id = subscription_id
    if status:
        profile.subscription_status = status

    if status in ACTIVE_SUBSCRIPTION_STATUSES:
        profile.plan = PLAN_PRO
    else:
        profile.plan = PLAN_FREE

    profile.save()
    logger.info(
        "Synced billing for user %s → plan=%s status=%s sub=%s",
        profile.user_id,
        profile.plan,
        profile.subscription_status,
        profile.dodo_subscription_id,
    )
    return profile


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
    from django.conf import settings as django_settings

    from core.services import dodo_service

    profile = get_or_create_profile(user_id)
    customer_id = profile.dodo_customer_id or None
    product_id = django_settings.DODO_PRO_PRODUCT_ID or None

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

    # Prefer an existing subscription id, then active, then any recent sub for the product.
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

    for status in ("active", "pending"):
        try:
            found = dodo_service.list_subscriptions_for_customer(
                customer_id,
                status=status,
                product_id=product_id,
            )
            candidates.extend(found)
        except Exception:
            logger.exception(
                "Failed listing %s subscriptions for customer %s", status, customer_id
            )

    if not candidates:
        try:
            candidates.extend(
                dodo_service.list_subscriptions_for_customer(
                    customer_id,
                    product_id=product_id,
                )
            )
        except Exception:
            logger.exception(
                "Failed listing subscriptions for customer %s", customer_id
            )

    # Deduplicate by subscription_id, prefer active.
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

    def sort_key(sub: Any) -> tuple[int, str]:
        status = _normalize_status(_attr(sub, "status")) or ""
        rank = 0 if status == "active" else 1 if status == "pending" else 2
        return (rank, _attr(sub, "subscription_id", "subscriptionId") or "")

    best = sorted(by_id.values(), key=sort_key)[0]
    apply_subscription_to_profile(profile, best)
    profile.reload()
    return billing_status_payload(user_id)
