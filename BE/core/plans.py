"""Plan limits for Free and Pro (Business comes later)."""

from __future__ import annotations

PLAN_FREE = "free"
PLAN_PRO = "pro"

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
}

PLATFORM_LABELS = {
    "reddit": "Reddit",
    "hackernews": "Hacker News",
    "twitter": "X",
    "youtube": "YouTube",
}


def limits_for_plan(plan: str) -> dict[str, int]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS[PLAN_FREE])
