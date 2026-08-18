"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Platform } from "@/lib/enums";
import { platforms } from "@/lib/platforms";
import { useApi, ApiUnauthorizedError, type BillingStatus } from "@/lib/api";
import {
  BILLING_UPGRADE_HREF,
  platformQuota,
} from "@/lib/billing";

type AddKeywordPlatformPickerProps = {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (platforms: Platform[]) => void;
};

export default function AddKeywordPlatformPicker({
  isOpen,
  onClose,
  onSelect,
}: AddKeywordPlatformPickerProps) {
  const api = useApi();
  const [selected, setSelected] = useState<Platform[]>([]);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [loadingBilling, setLoadingBilling] = useState(false);

  useEffect(() => {
    if (isOpen) setSelected([]);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    (async () => {
      try {
        setLoadingBilling(true);
        const status = await api.getBillingStatus();
        if (!cancelled) setBilling(status);
      } catch (err) {
        if (err instanceof ApiUnauthorizedError) return;
        if (!cancelled) setBilling(null);
      } finally {
        if (!cancelled) setLoadingBilling(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [isOpen, api]);

  const selectable = platforms.filter((p) => platformQuota(billing, p.id).available);
  const allSelectableIds = selectable.map((p) => p.id);
  const allSelected =
    allSelectableIds.length > 0 &&
    allSelectableIds.every((id) => selected.includes(id));

  const toggle = (id: Platform) => {
    const quota = platformQuota(billing, id);
    if (!quota.available) return;
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    setSelected(allSelected ? [] : [...allSelectableIds]);
  };

  const handleContinue = () => {
    if (selected.length === 0) return;
    onSelect(selected);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-white">
        <DialogHeader>
          <DialogTitle>Choose platforms</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-slate-500 mb-3">
          Select where this keyword should be monitored. Platforms at your plan
          limit are locked.
        </p>

        {billing?.canUpgrade && (
          <div className="mb-3 rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-xs text-indigo-800">
            On Free: Reddit & HN only (2 each).{" "}
            <Link href={BILLING_UPGRADE_HREF} className="font-semibold underline">
              Upgrade to Pro
            </Link>{" "}
            for X, YouTube, and higher limits.
          </div>
        )}

        <div className="flex items-center justify-between mb-3">
          <button
            type="button"
            onClick={toggleAll}
            disabled={allSelectableIds.length === 0}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-800 disabled:opacity-40"
          >
            {allSelected ? "Clear all" : "Select all available"}
          </button>
          <span className="text-xs text-slate-500">
            {loadingBilling ? "Loading limits…" : `${selected.length} selected`}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {platforms.map((p) => {
            const isSelected = selected.includes(p.id);
            const quota = platformQuota(billing, p.id);
            const disabled = !quota.available;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => toggle(p.id)}
                disabled={disabled}
                aria-pressed={isSelected}
                className={`flex flex-col gap-2 rounded-xl border p-4 text-left transition-colors ${
                  disabled
                    ? "border-slate-100 bg-slate-50 opacity-70 cursor-not-allowed"
                    : isSelected
                      ? "border-indigo-400 bg-indigo-50 ring-1 ring-indigo-200"
                      : "border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`flex h-5 w-5 shrink-0 items-center justify-center rounded border ${
                      isSelected
                        ? "border-indigo-600 bg-indigo-600 text-white"
                        : "border-slate-300 bg-white"
                    }`}
                  >
                    {isSelected && (
                      <svg className="h-3.5 w-3.5" viewBox="0 0 12 12" fill="none">
                        <path
                          d="M2 6l3 3 5-5"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    )}
                  </div>
                  <div className={`p-2 rounded-lg bg-slate-50 ${p.color}`}>{p.icon}</div>
                  <span className="font-medium text-slate-900">{p.name}</span>
                </div>
                <p className="text-[11px] text-slate-500 pl-8">
                  {quota.locked
                    ? "Requires Pro"
                    : quota.atLimit
                      ? `Limit reached (${quota.used}/${quota.limit})`
                      : `${quota.used} / ${quota.limit} used`}
                </p>
              </button>
            );
          })}
        </div>

        {selectable.length === 0 && !loadingBilling && (
          <p className="mt-3 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
            You&apos;ve hit every keyword limit on your plan.{" "}
            <Link href={BILLING_UPGRADE_HREF} className="font-semibold underline">
              Upgrade
            </Link>{" "}
            or remove a keyword to continue.
          </p>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleContinue}
            disabled={selected.length === 0}
            className="gradient-button"
          >
            Continue
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
