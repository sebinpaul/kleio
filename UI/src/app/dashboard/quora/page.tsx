"use client";

import PlatformDashboard from "@/components/PlatformDashboard";
import { getPlatformById } from "@/lib/platforms";

export default function QuoraDashboard() {
  const platform = getPlatformById("quora");
  if (!platform) return null;
  return <PlatformDashboard platform={platform} />;
}
