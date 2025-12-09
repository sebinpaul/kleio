import { ReactNode } from "react";
import { Platform as PlatformEnum } from "./enums";

export interface PlatformConfig {
  id: PlatformEnum;
  name: string;
  icon: ReactNode;
  description: string;
  color: string;
  defaultStats: Array<{
    title: string;
    value: string | number;
    description: string;
  }>;
}

export const platforms: PlatformConfig[] = [
  {
    id: PlatformEnum.REDDIT,
    name: "Reddit",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z" />
      </svg>
    ),
    description: "Monitor your keywords across Reddit subreddits",
    color: "text-orange-500",
    defaultStats: [
      {
        title: "Total Keywords",
        value: "0",
        description: "Active keywords",
      },
      {
        title: "Monitored Subreddits",
        value: "0",
        description: "Unique subreddits",
      },
      {
        title: "Mentions Today",
        value: "0",
        description: "New mentions",
      },
    ],
  },
  {
    id: PlatformEnum.FACEBOOK,
    name: "Facebook",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M22.675 0h-21.35C.595 0 0 .594 0 1.326v21.348C0 23.406.595 24 1.326 24H12.82v-9.294H9.692V11.08h3.128V8.413c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.794.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.314h3.587l-.467 3.626h-3.12V24h6.116C23.406 24 24 23.406 24 22.674V1.326C24 .594 23.406 0 22.675 0z"/>
      </svg>
    ),
    description: "Monitor public Facebook Pages (API or public fallback)",
    color: "text-blue-700",
    defaultStats: [
      { title: "Total Keywords", value: "0", description: "Active keywords" },
      { title: "Pages Tracked", value: "0", description: "Configured pages" },
      { title: "Mentions Today", value: "0", description: "New mentions" },
    ],
  },
  {
    id: PlatformEnum.YOUTUBE,
    name: "YouTube",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M23.498 6.186a2.995 2.995 0 00-2.109-2.12C19.483 3.5 12 3.5 12 3.5s-7.483 0-9.389.566A2.995 2.995 0 00.502 6.186 31.54 31.54 0 000 12a31.54 31.54 0 00.502 5.814 2.995 2.995 0 002.109 2.12C4.517 20.5 12 20.5 12 20.5s7.483 0 9.389-.566a2.995 2.995 0 002.109-2.12A31.54 31.54 0 0024 12a31.54 31.54 0 00-.502-5.814zM9.75 15.5v-7l6 3.5-6 3.5z" />
      </svg>
    ),
    description: "Monitor video titles and descriptions via Invidious",
    color: "text-red-600",
    defaultStats: [
      { title: "Total Keywords", value: "0", description: "Active keywords" },
      { title: "Videos Scanned", value: "0", description: "Recent videos" },
      { title: "Mentions Today", value: "0", description: "New mentions" },
    ],
  },
  {
    id: PlatformEnum.HACKERNEWS,
    name: "Hacker News",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M0 24V0h24v24H0zM6.951 5.896l4.112 15.173L19.088 5.896h-2.288l-2.219 8.2-4.036-8.2h-2.288z" />
      </svg>
    ),
    description: "Monitor your keywords across Hacker News",
    color: "text-orange-600",
    defaultStats: [
      {
        title: "Total Keywords",
        value: "0",
        description: "Active keywords",
      },
      {
        title: "Mentions Today",
        value: "0",
        description: "New mentions",
      },
      {
        title: "Top Stories",
        value: "0",
        description: "Stories monitored",
      },
    ],
  },
  {
    id: PlatformEnum.TWITTER,
    name: "Twitter",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
      </svg>
    ),
    description: "Track mentions across Twitter posts and conversations",
    color: "text-blue-500",
    defaultStats: [
      {
        title: "Total Keywords",
        value: "0",
        description: "Active keywords",
      },
      {
        title: "Tweets Monitored",
        value: "0",
        description: "Tweets scanned",
      },
      {
        title: "Mentions Today",
        value: "0",
        description: "New mentions",
      },
      {
        title: "Engagement Rate",
        value: "0%",
        description: "Average engagement",
      },
    ],
  },
  {
    id: PlatformEnum.LINKEDIN,
    name: "LinkedIn",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
    description: "Monitor professional conversations and company mentions",
    color: "text-blue-600",
    defaultStats: [
      {
        title: "Total Keywords",
        value: "0",
        description: "Active keywords",
      },
      {
        title: "Posts Monitored",
        value: "0",
        description: "LinkedIn posts",
      },
      {
        title: "Mentions Today",
        value: "0",
        description: "New mentions",
      },
      {
        title: "Professional Reach",
        value: "0",
        description: "Total impressions",
      },
    ],
  },
  {
    id: PlatformEnum.QUORA,
    name: "Quora",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 0C5.373 0 0 4.82 0 10.77 0 16.722 5.373 21.54 12 21.54c1.52 0 2.974-.243 4.313-.69l2.92 2.85c.208.205.548.06.548-.23v-4.87c2.961-1.957 4.219-4.778 4.219-7.83C24 4.82 18.627 0 12 0zm1.5 18.27c-3.584 0-6.49-2.87-6.49-6.407 0-3.538 2.906-6.406 6.49-6.406 3.583 0 6.49 2.868 6.49 6.406 0 3.537-2.907 6.407-6.49 6.407z"/>
      </svg>
    ),
    description: "Monitor questions, answers, and topics",
    color: "text-rose-600",
    defaultStats: [
      { title: "Total Keywords", value: "0", description: "Active keywords" },
      { title: "Items Scanned", value: "0", description: "Recent items" },
      { title: "Mentions Today", value: "0", description: "New mentions" },
    ],
  },
];

export function getPlatformById(id: string): PlatformConfig | undefined {
  return platforms.find((platform) => platform.id === id);
}
