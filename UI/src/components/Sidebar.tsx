"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UserButton } from "@clerk/nextjs";

const platforms = [
  {
    id: "overview",
    name: "Overview",
    href: "/dashboard",
    description: "All platforms overview",
    color: "from-indigo-500 to-purple-500",
    icon: (
      <div className="relative">
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
      </div>
    ),
  },
  {
    id: "reddit",
    name: "Reddit",
    description: "Monitor Reddit mentions",
    href: "/dashboard/reddit",
    color: "from-orange-500 to-red-500",
    icon: (
      <div className="relative">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z" />
        </svg>
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-orange-400 rounded-full"></div>
      </div>
    ),
  },
  {
    id: "hackernews",
    name: "Hacker News",
    href: "/dashboard/hackernews",
    description: "Monitor tech discussions",
    color: "from-orange-500 to-yellow-500",
    icon: (
      <div className="relative">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M0 24V0h24v24H0zM6.951 5.896l4.112 15.173L19.088 5.896h-2.288l-2.219 8.2-4.036-8.2h-2.288z" />
        </svg>
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
      </div>
    ),
  },
  {
    id: "twitter",
    name: "Twitter",
    href: "/dashboard/twitter",
    description: "Track social mentions",
    color: "from-blue-400 to-cyan-500",
    icon: (
      <div className="relative">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
        </svg>
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
      </div>
    ),
  },
  {
    id: "youtube",
    name: "YouTube",
    href: "/dashboard/youtube",
    description: "Monitor videos",
    color: "from-red-500 to-rose-500",
    icon: (
      <div className="relative">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.498 6.186a2.995 2.995 0 00-2.109-2.12C19.483 3.5 12 3.5 12 3.5s-7.483 0-9.389.566A2.995 2.995 0 00.502 6.186 31.54 31.54 0 000 12a31.54 31.54 0 00.502 5.814 2.995 2.995 0 002.109 2.12C4.517 20.5 12 20.5 12 20.5s7.483 0 9.389-.566a2.995 2.995 0 002.109-2.12A31.54 31.54 0 0024 12a31.54 31.54 0 00-.502-5.814zM9.75 15.5v-7l6 3.5-6 3.5z" />
        </svg>
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></div>
      </div>
    ),
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    href: "/dashboard/linkedin",
    description: "Professional network monitoring",
    color: "from-blue-600 to-indigo-600",
    icon: (
      <div className="relative">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
        </svg>
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-indigo-400 rounded-full"></div>
      </div>
    ),
  },
  {
    id: "facebook",
    name: "Facebook",
    href: "/dashboard/facebook",
    description: "Public Pages monitoring",
    color: "from-blue-700 to-sky-500",
    icon: (
      <div className="relative">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M22.675 0h-21.35C.595 0 0 .594 0 1.326v21.348C0 23.406.595 24 1.326 24H12.82v-9.294H9.692V11.08h3.128V8.413c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.794.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.314h3.587l-.467 3.626h-3.12V24h6.116C23.406 24 24 23.406 24 22.674V1.326C24 .594 23.406 0 22.675 0z"/>
        </svg>
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-blue-400 rounded-full"></div>
      </div>
    ),
  },
  {
    id: "quora",
    name: "Quora",
    href: "/dashboard/quora",
    description: "Questions & answers monitoring",
    color: "from-red-700 to-rose-500",
    icon: (
      <div className="relative">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0C5.373 0 0 4.82 0 10.77 0 16.722 5.373 21.54 12 21.54c1.52 0 2.974-.243 4.313-.69l2.92 2.85c.208.205.548.06.548-.23v-4.87c2.961-1.957 4.219-4.778 4.219-7.83C24 4.82 18.627 0 12 0zm1.5 18.27c-3.584 0-6.49-2.87-6.49-6.407 0-3.538 2.906-6.406 6.49-6.406 3.583 0 6.49 2.868 6.49 6.406 0 3.537-2.907 6.407-6.49 6.407z"/>
        </svg>
        <div className="absolute -top-1 -right-1 w-2 h-2 bg-rose-400 rounded-full"></div>
      </div>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white/95 backdrop-blur-lg border-r border-slate-200 shadow-xl">
      <div className="flex flex-col h-full">
        {/* Logo Section */}
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full animate-pulse"></div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Kleio</h1>
              <p className="text-sm text-slate-500">Keyword Monitor</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {platforms.map((platform) => {
            const isActive = pathname === platform.href;
            
            return (
              <Link
                key={platform.id}
                href={platform.href}
                className={`
                  group flex items-center space-x-3 px-3 py-3 rounded-xl font-medium text-sm transition-all duration-200
                  ${isActive 
                    ? 'bg-gradient-to-r from-indigo-50 to-purple-50 text-indigo-700 border-r-2 border-indigo-500 shadow-sm' 
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 nav-hover'
                  }
                `}
              >
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-lg transition-all duration-200
                  ${isActive 
                    ? 'bg-white shadow-sm text-indigo-600' 
                    : 'bg-slate-100 text-slate-500 group-hover:bg-white group-hover:text-slate-700 group-hover:shadow-sm'
                  }
                `}>
                  {platform.icon}
                </div>
                <div className="flex-1">
                  <div className="font-semibold">{platform.name}</div>
                  <div className="text-xs text-slate-500">{platform.description}</div>
                </div>
                <div className={`
                  w-2 h-2 rounded-full transition-all duration-200
                  ${isActive ? 'bg-indigo-400' : 'bg-slate-300 opacity-0 group-hover:opacity-100'}
                `}></div>
              </Link>
            );
          })}
        </nav>

        {/* Settings Section */}
        <div className="p-4 border-t border-slate-200">
          <Link
            href="/settings"
            className="group flex items-center space-x-3 px-3 py-3 rounded-xl font-medium text-sm text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all duration-200 nav-hover"
          >
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-slate-100 text-slate-500 group-hover:bg-white group-hover:text-slate-700 group-hover:shadow-sm transition-all duration-200">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <span>Settings</span>
          </Link>
        </div>

        {/* User Section */}
        <div className="p-4 border-t border-slate-200">
          <div className="flex items-center space-x-3 px-3 py-3 rounded-xl bg-gradient-to-r from-slate-50 to-indigo-50">
            <UserButton 
              appearance={{
                elements: {
                  avatarBox: "w-10 h-10"
                }
              }}
            />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-slate-900 truncate">Welcome back</div>
              <div className="text-xs text-slate-500">Monitoring active</div>
            </div>
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
