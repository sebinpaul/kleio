"use client";

import PlatformDashboard from "@/components/PlatformDashboard";
import { getPlatformById } from "@/lib/platforms";

export default function TwitterDashboard() {
  const platform = getPlatformById("twitter");
  if (!platform) return null;
  return <PlatformDashboard platform={platform} />;
}
