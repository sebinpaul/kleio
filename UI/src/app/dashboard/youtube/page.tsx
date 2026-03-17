"use client";

import PlatformDashboard from "@/components/PlatformDashboard";
import { getPlatformById } from "@/lib/platforms";

export default function YouTubeDashboard() {
  const platform = getPlatformById("youtube");
  if (!platform) return null;
  return <PlatformDashboard platform={platform} />;
}
