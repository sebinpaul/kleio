"use client";

import React, { useRef, useState } from "react";
import Link from "next/link";
import { platforms } from "@/lib/platforms";
import KeywordOverview, { KeywordOverviewRef } from "@/components/KeywordOverview";
import MentionsFeed from "@/components/MentionsFeed";
import KeywordModal from "@/components/KeywordModal";
import AddKeywordPlatformPicker from "@/components/AddKeywordPlatformPicker";
import { Platform } from "@/lib/enums";
import { Button } from "@/components/ui/button";

export default function Dashboard() {
  const overviewRef = useRef<KeywordOverviewRef>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | undefined>();

  const handleKeywordSaved = () => {
    setModalOpen(false);
    setSelectedPlatform(undefined);
    overviewRef.current?.refresh();
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
              className="gradient-button px-5 py-2.5 text-sm font-medium"
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
        onSelect={(platform) => {
          setSelectedPlatform(platform);
          setModalOpen(true);
        }}
      />

      <KeywordModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          setSelectedPlatform(undefined);
        }}
        onKeywordSaved={handleKeywordSaved}
        platform={selectedPlatform}
      />
    </div>
  );
}
