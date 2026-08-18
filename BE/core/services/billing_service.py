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


def _metadata_dict(raw: Any) -> dict[str, str]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items() if v is not None}
    # pydantic / SDK objects sometimes expose model_dump
    if hasattr(raw, "model_dump"):
        dumped = raw.model_dump()
        if isinstance(dumped, dict):
            return {str(k): str(v) for k, v in dumped.items() if v is not None}
    return {}


def _customer_id(subscription: Any) -> str | None:
    customer = getattr(subscription, "customer", None)
    if customer is None:
        return None
    if isinstance(customer, dict):
        return customer.get("customer_id") or customer.get("customerId")
    return getattr(customer, "customer_id", None)


def apply_subscription_event(subscription: Any) -> UserProfile | None:
    """Sync UserProfile from a Dodo subscription object (webhook data)."""
    metadata = _metadata_dict(getattr(subscription, "metadata", None))
    user_id = metadata.get("clerk_user_id") or metadata.get("user_id")
    subscription_id = getattr(subscription, "subscription_id", None)
    customer_id = _customer_id(subscription)
    status = getattr(subscription, "status", None)
    if isinstance(status, str):
        status = status.lower()
    else:
        status = str(status).lower() if status is not None else None

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

    if customer_id:
        profile.dodo_customer_id = customer_id
    if subscription_id:
        profile.dodo_subscription_id = subscription_id
    if status:
        profile.subscription_status = status

    if status in ACTIVE_SUBSCRIPTION_STATUSES:
        profile.plan = PLAN_PRO
    else:
        # cancelled / on_hold / expired / failed / paused → free access
        profile.plan = PLAN_FREE

    profile.save()
    logger.info(
        "Synced billing for user %s → plan=%s status=%s",
        profile.user_id,
        profile.plan,
        profile.subscription_status,
    )
    return profile
