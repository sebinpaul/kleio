"use client";

import PlatformDashboard from "@/components/PlatformDashboard";
import { getPlatformById } from "@/lib/platforms";

export default function FacebookDashboard() {
  const platform = getPlatformById("facebook");
  if (!platform) return null;
  return <PlatformDashboard platform={platform} />;
}
