"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import KeywordModal from "@/components/KeywordModal";
import KeywordList from "@/components/KeywordList";

export default function Dashboard() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Platform metrics with beautiful styling
  const platformMetrics = [
    {
      title: "Total Keywords",
      value: "1,247",
      change: "+12%",
      changeType: "positive" as const,
      description: "vs last month",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
        </svg>
      ),
    },
    {
      title: "Active Monitoring",
      value: "892",
      change: "+8%",
      changeType: "positive" as const,
      description: "currently tracking",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
              title: "Today&apos;s Mentions",
      value: "2,341",
      change: "+24%",
      changeType: "positive" as const,
      description: "across all platforms",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      title: "Response Rate",
      value: "94.2%",
      change: "+2%",
      changeType: "positive" as const,
      description: "system uptime",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
  ];

  // Platform quick access
  const platforms = [
    {
      name: "Reddit",
      description: "Track subreddit mentions",
      count: "324",
      href: "/dashboard/reddit",
      gradient: "gradient-button-reddit",
      bgColor: "bg-gradient-to-r from-orange-50 to-red-50",
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249z" />
        </svg>
      ),
    },
    {
      name: "Hacker News",
      description: "Monitor tech discussions",
      count: "156",
      href: "/dashboard/hackernews",
      gradient: "gradient-button-hackernews",
      bgColor: "bg-gradient-to-r from-orange-50 to-yellow-50",
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M0 24V0h24v24H0zM6.951 5.896l4.112 15.173L19.088 5.896h-2.288l-2.219 8.2-4.036-8.2h-2.288z" />
        </svg>
      ),
    },
    {
      name: "Twitter",
      description: "Track social mentions",
      count: "892",
      href: "/dashboard/twitter",
      gradient: "gradient-button-twitter",
      bgColor: "bg-gradient-to-r from-blue-50 to-cyan-50",
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
        </svg>
      ),
    },
    {
      name: "LinkedIn",
      description: "Professional network monitoring",
      count: "127",
      href: "/dashboard/linkedin",
      gradient: "gradient-button-linkedin",
      bgColor: "bg-gradient-to-r from-blue-50 to-indigo-50",
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Simplified Header - aligned with sidebar logo */}
      <div className="px-8 py-6">
        <h1 className="text-2xl font-semibold text-slate-900">
          Overview Dashboard
        </h1>
      </div>

      <div className="px-8 pb-8 space-y-8">
        {/* Statistics Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {platformMetrics.map((metric, index) => (
            <div key={index} className="metric-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="p-2.5 rounded-xl bg-indigo-100 text-indigo-600">
                  {metric.icon}
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                  metric.changeType === 'positive' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  {metric.changeType === 'positive' ? '↗' : '→'} Live
                </div>
              </div>
              
              <div className="space-y-1">
                <h3 className="text-base font-medium text-slate-600">{metric.title}</h3>
                <div className="text-3xl font-bold text-slate-900 mt-2">{metric.value}</div>
                                  <p className="text-sm text-slate-500">{metric.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Platform Quick Access */}
        <div className="enhanced-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Platform Overview</h2>
              <p className="text-sm text-slate-600 mt-1">Quick access to your monitoring platforms</p>
            </div>
            <div className="activity-dot success"></div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {platforms.map((platform) => (
              <a 
                key={platform.name}
                href={platform.href}
                className={`${platform.bgColor} p-4 rounded-xl border border-white/60 hover:shadow-md transition-all duration-200 group hover:scale-105`}
              >
                <div className="flex items-center space-x-3 mb-3">
                  <div className="text-slate-700">
                    {platform.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-900">{platform.name}</h3>
                    <p className="text-sm text-slate-600">{platform.description}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-slate-900">{platform.count}</span>
                  <span className="text-sm text-slate-500">active keywords</span>
                </div>
              </a>
            ))}
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Activity */}
          <div className="lg:col-span-2 enhanced-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">Recent Activity</h2>
                <p className="text-sm text-slate-600 mt-1">Latest mentions and updates</p>
              </div>
              <button className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-medium text-slate-700 transition-colors">
                View All
              </button>
            </div>

            <div className="space-y-4">
              {[
                { platform: "Reddit", action: "New mention detected", time: "2 minutes ago", status: "success" },
                { platform: "Twitter", action: "Keyword alert triggered", time: "5 minutes ago", status: "warning" },
                { platform: "LinkedIn", action: "Weekly report generated", time: "1 hour ago", status: "success" },
              ].map((activity, index) => (
                <div key={index} className="flex items-center space-x-4 p-3 bg-slate-50 rounded-lg">
                  <div className={`activity-dot ${activity.status}`}></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-900">{activity.action}</p>
                    <p className="text-xs text-slate-500">{activity.platform} • {activity.time}</p>
                  </div>
                  <button className="text-indigo-600 hover:text-indigo-700 text-xs font-medium">
                    View
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="enhanced-card p-6">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Stats</h3>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Active Monitors</span>
                <span className="text-lg font-semibold text-slate-900">24</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Today&apos;s Alerts</span>
                <span className="text-lg font-semibold text-emerald-600">12</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Response Time</span>
                <span className="text-lg font-semibold text-blue-600">1.2s</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Success Rate</span>
                <span className="text-lg font-semibold text-indigo-600">99.8%</span>
              </div>
            </div>

            <button 
              onClick={() => setIsAddModalOpen(true)}
              className="w-full mt-6 gradient-button p-3 text-sm font-medium"
            >
              Add New Keyword
            </button>
          </div>
        </div>

        {/* Keywords Management */}
        <div className="enhanced-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">Keywords Management</h2>
              <p className="text-sm text-slate-600 mt-1">Manage all your monitoring keywords across platforms</p>
            </div>
            <Button 
              onClick={() => setIsAddModalOpen(true)}
              className="gradient-button px-4 py-2 text-sm"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Keyword
            </Button>
          </div>
          
          <KeywordList onRefresh={() => {}} />
        </div>

        {/* Keyword Modal */}
        <KeywordModal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          onKeywordSaved={() => {
            setIsAddModalOpen(false);
          }}
        />
      </div>
    </div>
  );
}
