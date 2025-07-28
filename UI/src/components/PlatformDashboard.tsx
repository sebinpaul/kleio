"use client";

import React, { ReactNode, useRef } from "react";
import { Button } from "./ui/button";
import KeywordList, { KeywordListRef } from "./KeywordList";
import KeywordModal from "./KeywordModal";
import { Platform } from "@/lib/enums";

interface PlatformStats {
  title: string;
  value: string | number;
  description: string;
  icon?: ReactNode;
  color?: string;
}

interface PlatformDashboardProps {
  platform: {
    id: Platform;
    name: string;
    icon: ReactNode;
    description: string;
    color: string;
  };
  stats: PlatformStats[];
  isAddModalOpen: boolean;
  onAddModalOpen: () => void;
  onAddModalClose: () => void;
  onKeywordAdded: () => void;
}

export default function PlatformDashboard({
  platform,
  stats,
  isAddModalOpen,
  onAddModalOpen,
  onAddModalClose,
  onKeywordAdded,
}: PlatformDashboardProps) {
  const keywordListRef = useRef<KeywordListRef>(null);

  const handleKeywordSaved = () => {
    onAddModalClose();
    keywordListRef.current?.refresh();
    onKeywordAdded();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Simplified Header - aligned with sidebar logo */}
      <div className="px-8 py-6">
        <h1 className="text-2xl font-semibold text-slate-900">
          {platform.name} Dashboard
        </h1>
      </div>

      <div className="px-8 pb-8 space-y-8">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => {
            const icons = [
              <svg key="1" className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-1l-4 4z" />
              </svg>,
              <svg key="2" className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>,
              <svg key="3" className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 00-2-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H9z" />
              </svg>,
              <svg key="4" className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            ];
            
            const bgColors = ['bg-blue-100', 'bg-emerald-100', 'bg-purple-100', 'bg-orange-100'];
            
            return (
              <div key={index} className="metric-card p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600">{stat.title}</p>
                    <div className="text-5xl font-semibold text-slate-900 mt-2">{stat.value}</div>
                  </div>
                  <div className={`p-3 ${bgColors[index % bgColors.length]} rounded-xl`}>
                    {stat.icon || icons[index % icons.length]}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* PRIORITY: Keywords Management - Simplified */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Keywords Management</h2>
              <p className="text-sm text-slate-600 mt-1">Manage your {platform.name} monitoring keywords</p>
            </div>
            <Button
              onClick={onAddModalOpen}
              className="gradient-button px-6 py-2.5 text-sm font-medium"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Keyword
            </Button>
          </div>
          
          <KeywordList 
            ref={keywordListRef} 
            onRefresh={() => {}} 
            platform={platform.id}
          />
        </div>

        {/* Secondary Information Grid - Activity & Analytics */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Recent Activity - Takes more space */}
          <div className="lg:col-span-3 enhanced-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Recent Activity</h2>
                <p className="text-sm text-slate-600 mt-1">Latest mentions and interactions on {platform.name}</p>
              </div>
              <button className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-medium text-slate-700 transition-colors">
                View All
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                { 
                  type: `New mention detected`, 
                  content: "Great discussion about our product features and upcoming updates...", 
                  time: "2 minutes ago", 
                  engagement: 45, 
                  status: "positive" 
                },
                { 
                  type: `Keyword alert triggered`, 
                  content: "Community discussing best practices and implementation details...", 
                  time: "15 minutes ago", 
                  engagement: 23, 
                  status: "neutral" 
                },
                { 
                  type: `High engagement post`, 
                  content: "Comparison with competitors and feature analysis...", 
                  time: "1 hour ago", 
                  engagement: 78, 
                  status: "positive" 
                },
                { 
                  type: `Weekly summary`, 
                  content: "Performance metrics and trending keywords report...", 
                  time: "3 hours ago", 
                  engagement: 92, 
                  status: "positive" 
                }
              ].map((activity, index) => (
                <div key={index} className="flex items-start space-x-3 p-4 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors">
                  <div className={`p-2 rounded-lg flex-shrink-0 ${
                    activity.status === 'positive' ? 'bg-emerald-100 text-emerald-600' :
                    activity.status === 'neutral' ? 'bg-blue-100 text-blue-600' :
                    'bg-amber-100 text-amber-600'
                  }`}>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold text-slate-900 text-sm truncate">{activity.type}</h3>
                      <span className="text-xs text-slate-500 flex-shrink-0">{activity.time}</span>
                    </div>
                    <p className="text-sm text-slate-600 mb-2 line-clamp-2">{activity.content}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-slate-500">{activity.engagement} interactions</span>
                      <button className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                        View
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Performance & Actions Sidebar */}
          <div className="space-y-6">
            {/* Performance Overview */}
            <div className="enhanced-card p-4">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Performance</h3>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-600">Active Keywords</span>
                  <span className="text-sm font-semibold text-slate-900">24</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-600">Today&apos;s Mentions</span>
                  <span className="text-sm font-semibold text-emerald-600">127</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-600">Response Rate</span>
                  <span className="text-sm font-semibold text-blue-600">94.2%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-600">Avg. Engagement</span>
                  <span className="text-sm font-semibold text-indigo-600">8.7%</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-200">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-600">Trending</span>
                  <span className="text-emerald-600 font-medium">+12%</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="enhanced-card p-4">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h3>
              
              <div className="space-y-2">
                <Button
                  onClick={onAddModalOpen}
                  className="w-full gradient-button p-2.5 text-xs font-medium"
                >
                  <svg className="w-3 h-3 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Add Keyword
                </Button>
                
                <button className="w-full p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-medium transition-colors">
                  <svg className="w-3 h-3 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export Report
                </button>
                
                <button className="w-full p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-medium transition-colors">
                  <svg className="w-3 h-3 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Settings
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Add Keyword Modal */}
        <KeywordModal
          isOpen={isAddModalOpen}
          onClose={onAddModalClose}
          onKeywordSaved={handleKeywordSaved}
          platform={platform.id}
        />
      </div>
    </div>
  );
}
