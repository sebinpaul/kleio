"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import MentionsFeed from "@/components/MentionsFeed";
import { Platform } from "@/lib/enums";

function MentionsPageContent() {
  const searchParams = useSearchParams();
  const keywordId = searchParams.get("keywordId") || undefined;
  const keywordLabel = searchParams.get("keyword") || undefined;
  const platformParam = searchParams.get("platform");
  const platform =
    platformParam && Object.values(Platform).includes(platformParam as Platform)
      ? (platformParam as Platform)
      : undefined;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <div className="px-8 py-6 border-b border-slate-200/60 bg-white/60 backdrop-blur-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Mentions</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          All discovered matches across your keywords
        </p>
      </div>

      <div className="px-8 py-8">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <MentionsFeed
            platform={platform}
            keywordId={keywordId}
            keywordLabel={keywordLabel}
            pageSize={25}
            showFilters
          />
        </div>
      </div>
    </div>
  );
}

export default function MentionsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 animate-pulse">
          <div className="h-8 w-48 bg-slate-100 rounded mb-4" />
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 bg-slate-100 rounded-xl" />
            ))}
          </div>
        </div>
      }
    >
      <MentionsPageContent />
    </Suspense>
  );
}
