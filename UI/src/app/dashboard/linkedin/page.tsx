"use client";

import PlatformDashboard from "@/components/PlatformDashboard";
import { getPlatformById } from "@/lib/platforms";

export default function LinkedInDashboard() {
  const platform = getPlatformById("linkedin");
  if (!platform) return null;
  return <PlatformDashboard platform={platform} />;
}
