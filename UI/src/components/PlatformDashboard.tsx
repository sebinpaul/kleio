"use client";

import React, { ReactNode, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "./ui/button";
import KeywordOverview, { KeywordOverviewRef } from "@/components/KeywordOverview";
import MentionsFeed from "@/components/MentionsFeed";
import KeywordModal from "./KeywordModal";
import { Platform } from "@/lib/enums";
import { useApi, ApiUnauthorizedError, type BillingStatus } from "@/lib/api";
import { BILLING_UPGRADE_HREF, canAddOnPlatform, platformQuota } from "@/lib/billing";

interface PlatformDashboardProps {
  platform: {
    id: Platform;
    name: string;
    icon: ReactNode;
    description: string;
    color: string;
  };
}

export default function PlatformDashboard({ platform }: PlatformDashboardProps) {
  const api = useApi();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const overviewRef = useRef<KeywordOverviewRef>(null);

  const loadBilling = useCallback(async () => {
    try {
      const status = await api.getBillingStatus();
      setBilling(status);
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
    }
  }, [api]);

  useEffect(() => {
    loadBilling();
  }, [loadBilling]);

  const quota = platformQuota(billing, platform.id);
  const canAdd = canAddOnPlatform(billing, platform.id);

  const handleKeywordSaved = () => {
    setIsAddModalOpen(false);
    overviewRef.current?.refresh();
    loadBilling();
  };

  const handleAddClick = () => {
    if (!canAdd) return;
    setIsAddModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <div className="px-8 py-6 border-b border-slate-200/60 bg-white/60 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className={`p-2.5 rounded-xl bg-white shadow-sm border border-slate-200/80 ${platform.color}`}>
            {platform.icon}
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              {platform.name}
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">{platform.description}</p>
          </div>
        </div>
      </div>

      <div className="px-8 py-8">
        {!canAdd && billing && (
          <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {quota.locked ? (
              <>
                {platform.name} monitoring requires Pro.{" "}
                <Link href={BILLING_UPGRADE_HREF} className="font-semibold underline">
                  Upgrade to add keywords
                </Link>
                .
              </>
            ) : (
              <>
                You&apos;ve used {quota.used} / {quota.limit} {platform.name} keywords on your
                plan.{" "}
                <Link href={BILLING_UPGRADE_HREF} className="font-semibold underline">
                  Upgrade
                </Link>{" "}
                or remove a keyword to continue.
              </>
            )}
          </div>
        )}

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Keyword analytics</h2>
              <p className="text-sm text-slate-500 mt-0.5">
                Mentions over time, last activity, and status for your {platform.name} keywords
                {billing && !quota.locked && (
                  <span className="text-slate-400">
                    {" "}
                    · {quota.used}/{quota.limit} used
                  </span>
                )}
              </p>
            </div>
            <Button
              onClick={handleAddClick}
              disabled={!canAdd}
              title={
                !canAdd
                  ? quota.locked
                    ? "Requires Pro"
                    : "Plan limit reached"
                  : undefined
              }
              className="gradient-button px-5 py-2.5 text-sm font-medium disabled:opacity-50"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Keyword
            </Button>
          </div>

          <div className="p-6">
            <KeywordOverview
              ref={overviewRef}
              platform={platform.id}
              onAddKeyword={canAdd ? () => setIsAddModalOpen(true) : undefined}
            />
          </div>
        </div>

        <div className="mt-8 bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Recent mentions</h2>
              <p className="text-sm text-slate-500 mt-0.5">
                Latest {platform.name} matches for your keywords
              </p>
            </div>
            <Link
              href={`/dashboard/mentions?platform=${platform.id}`}
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              View all
            </Link>
          </div>
          <div className="p-6">
            <MentionsFeed
              platform={platform.id}
              compact
              pageSize={8}
              viewAllHref={`/dashboard/mentions?platform=${platform.id}`}
            />
          </div>
        </div>

        <KeywordModal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          onKeywordSaved={handleKeywordSaved}
          platform={platform.id}
        />
      </div>
    </div>
  );
}
