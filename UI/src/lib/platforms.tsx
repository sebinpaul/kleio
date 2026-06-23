import { ReactNode } from "react";
import { Platform as PlatformEnum } from "./enums";

export interface PlatformConfig {
  id: PlatformEnum;
  name: string;
  icon: ReactNode;
  description: string;
  color: string;
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
    description: "Monitor keywords across Reddit subreddits",
    color: "text-orange-500",
  },
  {
    id: PlatformEnum.HACKERNEWS,
    name: "Hacker News",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M0 24V0h24v24H0zM6.951 5.896l4.112 15.173L19.088 5.896h-2.288l-2.219 8.2-4.036-8.2h-2.288z" />
      </svg>
    ),
    description: "Monitor keywords across Hacker News",
    color: "text-orange-600",
  },
  {
    id: PlatformEnum.TWITTER,
    name: "Twitter",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
      </svg>
    ),
    description: "Track mentions across Twitter posts",
    color: "text-blue-500",
  },
  {
    id: PlatformEnum.YOUTUBE,
    name: "YouTube",
    icon: (
      <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 24 24">
        <path d="M23.498 6.186a2.995 2.995 0 00-2.109-2.12C19.483 3.5 12 3.5 12 3.5s-7.483 0-9.389.566A2.995 2.995 0 00.502 6.186 31.54 31.54 0 000 12a31.54 31.54 0 00.502 5.814 2.995 2.995 0 002.109 2.12C4.517 20.5 12 20.5 12 20.5s7.483 0 9.389-.566a2.995 2.995 0 002.109-2.12A31.54 31.54 0 0024 12a31.54 31.54 0 00-.502-5.814zM9.75 15.5v-7l6 3.5-6 3.5z" />
      </svg>
    ),
    description: "Monitor video titles and descriptions",
    color: "text-red-600",
  },
];

export function getPlatformById(id: string): PlatformConfig | undefined {
  return platforms.find((platform) => platform.id === id);
}
