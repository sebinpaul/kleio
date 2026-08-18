"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiUnauthorizedError,
  useApi,
  type BillingStatus,
  type KeywordSelectionPayload,
} from "@/lib/api";
import { BILLING_UPGRADE_HREF } from "@/lib/billing";
import Link from "next/link";

type Props = {
  onComplete: (status: BillingStatus) => void;
  onError?: (message: string) => void;
};

function initialSelected(payload: KeywordSelectionPayload): Set<string> {
  const selected = new Set<string>();
  for (const platform of payload.platforms) {
    if (platform.locked) continue;
    if (platform.requiresSelection) {
      // Prefer previously enabled; otherwise leave empty so the user chooses.
      for (const kw of platform.keywords) {
        if (kw.enabled) selected.add(kw.id);
      }
      continue;
    }
    // Under-cap platforms: keep whatever is still active.
    for (const kw of platform.keywords) {
      if (kw.enabled) selected.add(kw.id);
    }
  }
  return selected;
}

export default function KeywordSelectionPanel({ onComplete, onError }: Props) {
  const api = useApi();
  const [payload, setPayload] = useState<KeywordSelectionPayload | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setLocalError(null);
      const data = await api.getKeywordSelection();
      setPayload(data);
      setSelected(initialSelected(data));
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      const message =
        err instanceof Error ? err.message : "Failed to load keywords to keep";
      setLocalError(message);
      onError?.(message);
    } finally {
      setLoading(false);
    }
  }, [api, onError]);

  useEffect(() => {
    load();
  }, [load]);

  const countsByPlatform = useMemo(() => {
    const counts: Record<string, number> = {};
    if (!payload) return counts;
    for (const platform of payload.platforms) {
      counts[platform.platform] = platform.keywords.filter((k) =>
        selected.has(k.id)
      ).length;
    }
    return counts;
  }, [payload, selected]);

  const canSave = useMemo(() => {
    if (!payload) return false;
    for (const platform of payload.platforms) {
      if (platform.locked) continue;
      const count = countsByPlatform[platform.platform] ?? 0;
      if (count > platform.limit) return false;
      if (platform.requiresSelection && count > platform.limit) return false;
    }
    return true;
  }, [payload, countsByPlatform]);

  const toggle = (platformLimit: number, id: string, platformKey: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        return next;
      }
      const current =
        payload?.platforms
          .find((p) => p.platform === platformKey)
          ?.keywords.filter((k) => next.has(k.id)).length ?? 0;
      if (current >= platformLimit) return prev;
      next.add(id);
      return next;
    });
  };

  const handleSave = async () => {
    if (!payload || !canSave) return;
    setSaving(true);
    setLocalError(null);
    try {
      // Include under-cap active picks + over-cap choices.
      const keepIds = Array.from(selected);
      const status = await api.applyKeywordSelection(keepIds);
      onComplete(status);
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      const message =
        err instanceof Error ? err.message : "Failed to save keyword selection";
      setLocalError(message);
      onError?.(message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50/80 p-6 animate-pulse">
        <div className="h-5 w-48 bg-amber-100 rounded mb-3" />
        <div className="h-24 bg-amber-100/80 rounded-xl" />
      </div>
    );
  }

  if (!payload) {
    return localError ? (
      <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {localError}
      </div>
    ) : null;
  }

  const needsPick = payload.platforms.some((p) => p.requiresSelection);
  const lockedPlatforms = payload.platforms.filter((p) => p.locked && p.keywords.length);

  return (
    <div
      id="keyword-selection"
      className="scroll-mt-8 overflow-hidden rounded-2xl border border-amber-200 bg-white shadow-sm"
    >
      <div className="bg-gradient-to-br from-amber-500 via-amber-500 to-orange-500 px-6 py-5 text-white">
        <p className="text-xs font-medium uppercase tracking-wider text-white/80">
          Plan change
        </p>
        <h2 className="mt-1 text-xl font-bold tracking-tight">
          Choose keywords to keep
        </h2>
        <p className="mt-2 text-sm text-white/85 max-w-xl">
          {needsPick
            ? "You're over Free limits. Pick which keywords stay active — the rest pause until you upgrade or free up a slot."
            : "Confirm which keywords stay active on Free. Paused keywords are kept but not monitored."}
        </p>
      </div>

      <div className="p-6 space-y-5">
        {localError && (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            {localError}
          </div>
        )}

        {payload.platforms
          .filter((p) => !p.locked)
          .map((platform) => {
            const count = countsByPlatform[platform.platform] ?? 0;
            const atLimit = count >= platform.limit;
            return (
              <div key={platform.platform} className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">
                      {platform.label}
                    </h3>
                    <p className="text-xs text-slate-500">
                      {platform.requiresSelection
                        ? `Pick up to ${platform.limit}`
                        : `Up to ${platform.limit} active`}
                    </p>
                  </div>
                  <span
                    className={`tabular-nums text-xs font-medium px-2 py-1 rounded-full ${
                      count > platform.limit
                        ? "bg-red-100 text-red-700"
                        : atLimit
                          ? "bg-amber-100 text-amber-800"
                          : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {count} / {platform.limit}
                  </span>
                </div>
                <ul className="space-y-1.5">
                  {platform.keywords.map((kw) => {
                    const checked = selected.has(kw.id);
                    const disabled = !checked && atLimit;
                    return (
                      <li key={kw.id}>
                        <label
                          className={`flex items-center gap-3 rounded-lg border px-3 py-2.5 text-sm cursor-pointer transition-colors ${
                            checked
                              ? "border-indigo-200 bg-indigo-50/70"
                              : disabled
                                ? "border-slate-100 bg-slate-50 opacity-60 cursor-not-allowed"
                                : "border-slate-200 bg-white hover:bg-slate-50"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            disabled={disabled}
                            onChange={() =>
                              toggle(platform.limit, kw.id, platform.platform)
                            }
                            className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="font-medium text-slate-800 flex-1 truncate">
                            {kw.keyword}
                          </span>
                          {!kw.enabled && !checked && (
                            <span className="text-[11px] uppercase tracking-wide text-slate-400">
                              Paused
                            </span>
                          )}
                        </label>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}

        {lockedPlatforms.length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 space-y-2">
            <p className="text-sm font-semibold text-slate-800">
              Paused — Pro only
            </p>
            <p className="text-xs text-slate-500">
              These stay in your account but won&apos;t monitor on Free.{" "}
              <Link
                href={BILLING_UPGRADE_HREF}
                className="text-indigo-600 hover:text-indigo-700 font-medium"
              >
                Upgrade to Pro
              </Link>{" "}
              to turn them back on.
            </p>
            <ul className="space-y-1">
              {lockedPlatforms.map((platform) => (
                <li key={platform.platform} className="text-sm text-slate-600">
                  <span className="font-medium text-slate-800">
                    {platform.label}:
                  </span>{" "}
                  {platform.keywords.map((k) => k.keyword).join(", ")}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap gap-3 pt-1">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving || !canSave}
            className="gradient-button px-5 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save selection"}
          </button>
          <Link
            href={BILLING_UPGRADE_HREF}
            className="px-5 py-2.5 rounded-lg text-sm font-medium border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
          >
            Upgrade to Pro instead
          </Link>
        </div>
      </div>
    </div>
  );
}
