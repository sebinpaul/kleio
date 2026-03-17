"use client";

import React, { ReactNode, useRef, useState } from "react";
import { Button } from "./ui/button";
import KeywordList, { KeywordListRef } from "./KeywordList";
import KeywordModal from "./KeywordModal";
import { Platform } from "@/lib/enums";

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
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const keywordListRef = useRef<KeywordListRef>(null);

  const handleKeywordSaved = () => {
    setIsAddModalOpen(false);
    keywordListRef.current?.refresh();
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
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between px-6 py-5 border-b border-slate-100">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Keywords</h2>
              <p className="text-sm text-slate-500 mt-0.5">
                Manage your {platform.name} monitoring keywords
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
            <KeywordList
              ref={keywordListRef}
              onRefresh={() => {}}
              platform={platform.id}
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
