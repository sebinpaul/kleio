"use client";

import React, { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useApi, ApiUnauthorizedError, type BillingStatus } from "@/lib/api";

const PLATFORM_ROWS: { key: string; label: string }[] = [
  { key: "reddit", label: "Reddit" },
  { key: "hackernews", label: "Hacker News" },
  { key: "twitter", label: "X" },
  { key: "youtube", label: "YouTube" },
];

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

  const planLabel = billing?.plan === "pro" ? "Pro" : "Free";

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <div className="px-8 py-6 border-b border-slate-200/60 bg-white/60 backdrop-blur-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">Billing and notification preferences</p>
      </div>

      <div className="px-8 py-8 max-w-xl space-y-6">
        {loading ? (
          <div className="h-40 bg-slate-100 rounded-xl animate-pulse" />
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

            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5">
              <div>
                <h2 className="text-base font-semibold text-slate-900">Plan</h2>
                <p className="text-sm text-slate-500 mt-1">
                  You are on the <span className="font-medium text-slate-800">{planLabel}</span> plan
                  {billing?.subscriptionStatus
                    ? ` · subscription ${billing.subscriptionStatus}`
                    : ""}
                  .
                </p>
              </div>

              {billing && (
                <ul className="space-y-2">
                  {PLATFORM_ROWS.map(({ key, label }) => {
                    const used = billing.usage[key] ?? 0;
                    const limit = billing.limits[key] ?? 0;
                    return (
                      <li
                        key={key}
                        className="flex items-center justify-between text-sm rounded-lg border border-slate-100 bg-slate-50 px-3 py-2"
                      >
                        <span className="text-slate-700">{label}</span>
                        <span className="tabular-nums text-slate-500">
                          {used} / {limit === 0 ? "—" : limit}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              )}

              <div className="flex flex-wrap gap-3">
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
