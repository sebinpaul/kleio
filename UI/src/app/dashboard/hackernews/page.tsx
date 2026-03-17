"use client";

import PlatformDashboard from "@/components/PlatformDashboard";
import { getPlatformById } from "@/lib/platforms";

export default function HackerNewsDashboard() {
  const platform = getPlatformById("hackernews");
  if (!platform) return null;
  return <PlatformDashboard platform={platform} />;
}
