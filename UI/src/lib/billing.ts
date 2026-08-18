import type { BillingStatus } from "./api";
import { Platform } from "./enums";

export type PlatformQuota = {
  used: number;
  limit: number;
  remaining: number;
  /** Limit > 0 and under the cap */
  available: boolean;
  /** Plan does not include this platform (limit 0) */
  locked: boolean;
  /** At or over the cap */
  atLimit: boolean;
};

export function platformQuota(
  billing: BillingStatus | null | undefined,
  platform: string
): PlatformQuota {
  // Optimistic until billing loads — API still enforces hard limits.
  if (!billing) {
    return {
      used: 0,
      limit: 1,
      remaining: 1,
      available: true,
      locked: false,
      atLimit: false,
    };
  }
  const used = billing.usage?.[platform] ?? 0;
  const limit = billing.limits?.[platform] ?? 0;
  const remaining = Math.max(0, limit - used);
  const locked = limit <= 0;
  const atLimit = !locked && used >= limit;
  return {
    used,
    limit,
    remaining,
    available: !locked && used < limit,
    locked,
    atLimit,
  };
}

export function canAddOnPlatform(
  billing: BillingStatus | null | undefined,
  platform: string
): boolean {
  return platformQuota(billing, platform).available;
}

/** True if at least one platform still has room for a new keyword. */
export function canAddAnyKeyword(billing: BillingStatus | null | undefined): boolean {
  if (!billing) return true;
  return Object.keys(billing.limits).some((p) => canAddOnPlatform(billing, p));
}

export function planDisplayName(plan: string | undefined): string {
  if (plan === "pro") return "Pro";
  return "Free";
}

export const BILLING_SETTINGS_HREF = "/dashboard/settings#billing";
export const BILLING_UPGRADE_HREF = "/dashboard/settings?upgrade=pro#billing";
export const KEYWORD_SELECTION_HREF = "/dashboard/settings#keyword-selection";

export const METERED_PLATFORMS: Platform[] = [
  Platform.REDDIT,
  Platform.HACKERNEWS,
  Platform.TWITTER,
  Platform.YOUTUBE,
];
