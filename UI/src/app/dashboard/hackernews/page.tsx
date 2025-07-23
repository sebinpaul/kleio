"use client";

import { useState } from "react";
import PlatformDashboard from "../../../components/PlatformDashboard";
import { getPlatformById } from "../../../lib/platforms";

export default function HackerNewsDashboard() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const platform = getPlatformById("hackernews");

  if (!platform) return null;

  return (
    <PlatformDashboard
      platform={platform}
      stats={platform.defaultStats}
      isAddModalOpen={isAddModalOpen}
      onAddModalOpen={() => setIsAddModalOpen(true)}
      onAddModalClose={() => setIsAddModalOpen(false)}
      onKeywordAdded={() => {}}
    />
  );
}
