"""Plan limits for Free, Pro ($17), and Business ($75)."""

from __future__ import annotations

from django.conf import settings

PLAN_FREE = "free"
PLAN_PRO = "pro"
PLAN_BUSINESS = "business"

PAID_PLANS = frozenset({PLAN_PRO, PLAN_BUSINESS})

PLAN_RANK = {
    PLAN_FREE: 0,
    PLAN_PRO: 1,
    PLAN_BUSINESS: 2,
}

ACTIVE_SUBSCRIPTION_STATUSES = frozenset({"active"})

# Per-platform keyword caps. Platform keys match Platform enum values.
PLAN_LIMITS: dict[str, dict[str, int]] = {
    PLAN_FREE: {
        "reddit": 2,
        "hackernews": 2,
        "twitter": 0,
        "youtube": 0,
    },
    PLAN_PRO: {
        "reddit": 20,
        "hackernews": 20,
        "twitter": 4,
        "youtube": 4,
    },
    PLAN_BUSINESS: {
        "reddit": 100,
        "hackernews": 100,
        "twitter": 10,
        "youtube": 10,
    },
}

PLAN_PRICES = {
    PLAN_FREE: 0,
    PLAN_PRO: 17,
    PLAN_BUSINESS: 75,
}

PLAN_DISPLAY_NAMES = {
    PLAN_FREE: "Free",
    PLAN_PRO: "Pro",
    PLAN_BUSINESS: "Business",
}

PLATFORM_LABELS = {
    "reddit": "Reddit",
    "hackernews": "Hacker News",
    "twitter": "X",
    "youtube": "YouTube",
}

CHECKOUT_PLANS = frozenset({PLAN_PRO, PLAN_BUSINESS})


def limits_for_plan(plan: str) -> dict[str, int]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[PLAN_FREE])


def is_paid_plan(plan: str) -> bool:
    return plan in PAID_PLANS


def plan_rank(plan: str) -> int:
    return PLAN_RANK.get(plan, 0)


def normalize_checkout_plan(plan: str | None) -> str:
    """Return a valid checkout plan slug; default Pro."""
    value = (plan or PLAN_PRO).strip().lower()
    if value not in CHECKOUT_PLANS:
        raise ValueError("Invalid plan. Choose 'pro' or 'business'.")
    return value


def product_id_for_plan(plan: str) -> str:
    if plan == PLAN_PRO:
        product_id = settings.DODO_PRO_PRODUCT_ID
        if not product_id:
            raise RuntimeError("DODO_PRO_PRODUCT_ID is not configured")
        return product_id
    if plan == PLAN_BUSINESS:
        product_id = settings.DODO_BUSINESS_PRODUCT_ID
        if not product_id:
            raise RuntimeError("DODO_BUSINESS_PRODUCT_ID is not configured")
        return product_id
    raise ValueError(f"No Dodo product for plan: {plan}")


def plan_for_product_id(product_id: str | None) -> str | None:
    if not product_id:
        return None
    if product_id == settings.DODO_PRO_PRODUCT_ID:
        return PLAN_PRO
    if product_id and product_id == settings.DODO_BUSINESS_PRODUCT_ID:
        return PLAN_BUSINESS
    return None


def known_product_ids() -> list[str]:
    ids: list[str] = []
    if settings.DODO_PRO_PRODUCT_ID:
        ids.append(settings.DODO_PRO_PRODUCT_ID)
    if settings.DODO_BUSINESS_PRODUCT_ID:
        ids.append(settings.DODO_BUSINESS_PRODUCT_ID)
    return ids
