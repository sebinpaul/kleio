"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { platforms } from "@/lib/platforms";
import KeywordOverview, { KeywordOverviewRef } from "@/components/KeywordOverview";
import MentionsFeed from "@/components/MentionsFeed";
import KeywordModal from "@/components/KeywordModal";
import AddKeywordPlatformPicker from "@/components/AddKeywordPlatformPicker";
import { Platform } from "@/lib/enums";
import { Button } from "@/components/ui/button";
import { useApi, ApiUnauthorizedError, type BillingStatus } from "@/lib/api";
import { BILLING_UPGRADE_HREF, canAddAnyKeyword } from "@/lib/billing";

export default function Dashboard() {
  const api = useApi();
  const overviewRef = useRef<KeywordOverviewRef>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([]);
  const [billing, setBilling] = useState<BillingStatus | null>(null);

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

  const canAdd = canAddAnyKeyword(billing);

  const handleKeywordSaved = () => {
    setModalOpen(false);
    setSelectedPlatforms([]);
    overviewRef.current?.refresh();
    loadBilling();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <div className="px-8 py-6 border-b border-slate-200/60 bg-white/60 backdrop-blur-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Overview</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          All keywords and mention activity across platforms
        </p>
      </div>

      <div className="px-8 py-8 space-y-8">
        {!canAdd && billing && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            You&apos;ve hit your keyword limits on every available platform.{" "}
            <Link href={BILLING_UPGRADE_HREF} className="font-semibold underline">
              Upgrade your plan
            </Link>{" "}
            or remove a keyword to add more.
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {platforms.map((p) => (
            <Link
              key={p.id}
              href={`/dashboard/${p.id}`}
              className="group flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 hover:border-indigo-200 hover:shadow-md transition-all"
            >
              <div className={`p-2 rounded-lg bg-slate-50 group-hover:bg-indigo-50 transition-colors ${p.color}`}>
                {p.icon}
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-900 truncate">{p.name}</p>
                <p className="text-xs text-slate-500 truncate">{p.description}</p>
              </div>
            </Link>
          ))}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Keyword analytics</h2>
              <p className="text-sm text-slate-500 mt-0.5">
                Mentions over time, last activity, and platform for each keyword
              </p>
            </div>
            <Button
              onClick={() => setPickerOpen(true)}
              disabled={!canAdd}
              className="gradient-button px-5 py-2.5 text-sm font-medium disabled:opacity-50"
            >
              Add Keyword
            </Button>
          </div>
          <div className="p-6">
            <KeywordOverview ref={overviewRef} />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Recent mentions</h2>
              <p className="text-sm text-slate-500 mt-0.5">Latest matches across all platforms</p>
            </div>
            <Link
              href="/dashboard/mentions"
              className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
            >
              View all
            </Link>
          </div>
          <div className="p-6">
            <MentionsFeed compact pageSize={8} viewAllHref="/dashboard/mentions" />
          </div>
        </div>
      </div>

      <AddKeywordPlatformPicker
        isOpen={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onSelect={(picked) => {
          setSelectedPlatforms(picked);
          setModalOpen(true);
        }}
      />

      <KeywordModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedPlatforms([]);
        }}
        onKeywordSaved={handleKeywordSaved}
        platforms={selectedPlatforms}
        platform={
          selectedPlatforms.length === 1 ? selectedPlatforms[0] : undefined
        }
      />
    </div>
  );
}
