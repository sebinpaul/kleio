"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import KeywordModal from "@/components/KeywordModal";
import KeywordList from "@/components/KeywordList";
import { platforms } from "@/lib/platforms";

export default function Dashboard() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <div className="px-8 py-6 border-b border-slate-200/60 bg-white/60 backdrop-blur-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Overview</h1>
        <p className="text-sm text-slate-500 mt-0.5">All platforms at a glance</p>
      </div>

      <div className="px-8 py-8 space-y-8">
        {/* Platform Grid */}
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

        {/* All-platform Keywords */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">All Keywords</h2>
              <p className="text-sm text-slate-500 mt-0.5">
                Keywords across all platforms
              </p>
            </div>
            <Button
              onClick={() => setIsAddModalOpen(true)}
              className="gradient-button px-5 py-2.5 text-sm font-medium"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Keyword
            </Button>
          </div>

          <div className="p-6">
            <KeywordList onRefresh={() => {}} />
          </div>
        </div>

        <KeywordModal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          onKeywordSaved={() => setIsAddModalOpen(false)}
        />
      </div>
    </div>
  );
}
