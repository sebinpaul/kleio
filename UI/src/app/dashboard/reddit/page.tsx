"use client";

import PlatformDashboard from "@/components/PlatformDashboard";
import { getPlatformById } from "@/lib/platforms";

export default function RedditDashboard() {
  const platform = getPlatformById("reddit");
  if (!platform) return null;
  return <PlatformDashboard platform={platform} />;
}
