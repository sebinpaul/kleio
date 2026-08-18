"use client";

import React, { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useApi, ApiUnauthorizedError, type BillingStatus } from "@/lib/api";
import { planDisplayName } from "@/lib/billing";

const PLATFORM_ROWS: { key: string; label: string }[] = [
  { key: "reddit", label: "Reddit" },
  { key: "hackernews", label: "Hacker News" },
  { key: "twitter", label: "X" },
  { key: "youtube", label: "YouTube" },
];

const PRO_HIGHLIGHTS = [
  "20 Reddit + 20 HN keywords",
  "X and YouTube monitoring",
  "Higher alert capacity",
];

function usagePercent(used: number, limit: number): number {
  if (limit <= 0) return used > 0 ? 100 : 0;
  return Math.min(100, Math.round((used / limit) * 100));
}

function barColor(used: number, limit: number): string {
  if (limit <= 0) return "bg-slate-300";
  const pct = used / limit;
  if (pct >= 1) return "bg-amber-500";
  if (pct >= 0.75) return "bg-indigo-500";
  return "bg-emerald-500";
}

function SettingsPageContent() {
  const api = useApi();
  const searchParams = useSearchParams();
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [billingBusy, setBillingBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [billingMessage, setBillingMessage] = useState<string | null>(null);
  const upgradeStarted = useRef(false);
  const billingSectionRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [settings, billingStatus] = await Promise.all([
        api.getNotificationSettings(),
        api.getBillingStatus(),
      ]);
      setEmailNotifications(settings.emailNotifications);
      setBilling(billingStatus);
      setError(null);
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const billingParam = searchParams.get("billing");
    if (billingParam === "success") {
      setBillingMessage("Payment received. Your Pro plan will activate shortly.");
      load();
    } else if (billingParam === "cancelled") {
      setBillingMessage("Checkout cancelled. You can upgrade anytime.");
    }
  }, [searchParams, load]);

  useEffect(() => {
    if (loading) return;
    if (typeof window === "undefined") return;
    if (window.location.hash !== "#billing") return;
    billingSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [loading]);

  useEffect(() => {
    const shouldUpgrade =
      searchParams.get("upgrade") === "pro" &&
      billing?.canUpgrade &&
      !upgradeStarted.current &&
      !loading;

    if (!shouldUpgrade) return;

    upgradeStarted.current = true;
    (async () => {
      try {
        setBillingBusy(true);
        const { checkoutUrl } = await api.createBillingCheckout();
        window.location.href = checkoutUrl;
      } catch (err) {
        if (err instanceof ApiUnauthorizedError) return;
        setError(err instanceof Error ? err.message : "Failed to start checkout");
        upgradeStarted.current = false;
        setBillingBusy(false);
      }
    })();
  }, [searchParams, billing, loading, api]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await api.updateNotificationSettings({ emailNotifications });
      setSaved(true);
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleUpgrade = async () => {
    setBillingBusy(true);
    setError(null);
    try {
      const { checkoutUrl } = await api.createBillingCheckout();
      window.location.href = checkoutUrl;
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      setError(err instanceof Error ? err.message : "Failed to start checkout");
      setBillingBusy(false);
    }
  };

  const handleManageBilling = async () => {
    setBillingBusy(true);
    setError(null);
    try {
      const { portalUrl } = await api.createBillingPortal();
      window.location.href = portalUrl;
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      setError(err instanceof Error ? err.message : "Failed to open billing portal");
      setBillingBusy(false);
    }
  };

  const isPro = billing?.plan === "pro";
  const planLabel = planDisplayName(billing?.plan);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <div className="px-8 py-6 border-b border-slate-200/60 bg-white/60 backdrop-blur-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">Billing and notification preferences</p>
      </div>

      <div className="px-8 py-8 max-w-2xl space-y-6">
        {loading ? (
          <div className="h-64 bg-slate-100 rounded-2xl animate-pulse" />
        ) : (
          <>
            {error && (
              <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                {error}
              </div>
            )}
            {billingMessage && (
              <div className="text-sm text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-3">
                {billingMessage}
              </div>
            )}
            {saved && (
              <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
                Settings saved.
              </div>
            )}

            <div
              id="billing"
              ref={billingSectionRef}
              className="scroll-mt-8 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm"
            >
              <div
                className={`relative px-6 pt-6 pb-5 ${
                  isPro
                    ? "bg-gradient-to-br from-indigo-600 via-indigo-600 to-cyan-600 text-white"
                    : "bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white"
                }`}
              >
                <div className="absolute inset-0 opacity-30 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-white/40 via-transparent to-transparent pointer-events-none" />
                <div className="relative flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-white/70">
                      Current plan
                    </p>
                    <div className="mt-1 flex items-baseline gap-2">
                      <h2 className="text-3xl font-bold tracking-tight">{planLabel}</h2>
                      <span className="text-sm text-white/80">
                        {isPro ? "$17/mo" : "$0/mo"}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-white/75 max-w-md">
                      {isPro
                        ? "Full platform coverage across Reddit, HN, X, and YouTube."
                        : "Reddit and Hacker News starter limits. Upgrade for X, YouTube, and more keywords."}
                    </p>
                    {billing?.subscriptionStatus && (
                      <p className="mt-2 text-xs text-white/60 capitalize">
                        Subscription · {billing.subscriptionStatus}
                      </p>
                    )}
                  </div>
                  <span
                    className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${
                      isPro
                        ? "bg-white/20 text-white ring-1 ring-white/30"
                        : "bg-white/10 text-white/90 ring-1 ring-white/20"
                    }`}
                  >
                    {isPro ? "Active" : "Starter"}
                  </span>
                </div>
              </div>

              <div className="p-6 space-y-5">
                {billing && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-slate-900">
                        Keyword usage
                      </h3>
                      <span className="text-xs text-slate-500">
                        Hard limits by platform
                      </span>
                    </div>
                    <ul className="space-y-3">
                      {PLATFORM_ROWS.map(({ key, label }) => {
                        const used = billing.usage[key] ?? 0;
                        const limit = billing.limits[key] ?? 0;
                        const locked = limit <= 0;
                        const pct = usagePercent(used, limit);
                        return (
                          <li key={key} className="space-y-1.5">
                            <div className="flex items-center justify-between text-sm">
                              <span className="font-medium text-slate-800">{label}</span>
                              <span className="tabular-nums text-slate-500">
                                {locked ? (
                                  <span className="text-amber-700">Pro only</span>
                                ) : (
                                  <>
                                    {used}
                                    <span className="text-slate-400"> / {limit}</span>
                                  </>
                                )}
                              </span>
                            </div>
                            <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${barColor(used, limit)} ${
                                  locked ? "opacity-40" : ""
                                }`}
                                style={{ width: locked ? "100%" : `${pct}%` }}
                              />
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}

                {!isPro && (
                  <div className="rounded-xl border border-indigo-100 bg-indigo-50/60 px-4 py-3">
                    <p className="text-sm font-semibold text-indigo-900">
                      Unlock with Pro — $17/mo
                    </p>
                    <ul className="mt-2 space-y-1">
                      {PRO_HIGHLIGHTS.map((item) => (
                        <li
                          key={item}
                          className="flex items-center gap-2 text-sm text-indigo-800/90"
                        >
                          <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex flex-wrap gap-3 pt-1">
                  {billing?.canUpgrade && (
                    <button
                      onClick={handleUpgrade}
                      disabled={billingBusy}
                      className="gradient-button px-5 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50"
                    >
                      {billingBusy ? "Redirecting…" : "Upgrade to Pro — $17/mo"}
                    </button>
                  )}
                  {billing?.canManageBilling && (
                    <button
                      onClick={handleManageBilling}
                      disabled={billingBusy}
                      className="px-5 py-2.5 rounded-lg text-sm font-medium border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                      Manage billing
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
              <div>
                <h2 className="text-base font-semibold text-slate-900">Email notifications</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Master switch for mention alert emails. Per-keyword toggles in each keyword&apos;s
                  settings still apply.
                </p>
                <label className="mt-4 flex items-center gap-3 cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={emailNotifications}
                    onChange={(e) => setEmailNotifications(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-slate-700">
                    Send email alerts for new mentions
                  </span>
                </label>
              </div>

              <button
                onClick={handleSave}
                disabled={saving}
                className="gradient-button px-5 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save settings"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 animate-pulse">
          <div className="h-8 w-48 bg-slate-100 rounded mb-6" />
          <div className="h-40 bg-slate-100 rounded-xl" />
        </div>
      }
    >
      <SettingsPageContent />
    </Suspense>
  );
}
