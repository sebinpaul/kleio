"use client";

import { useState } from "react";
import PlatformDashboard from "../../../components/PlatformDashboard";
import { getPlatformById } from "../../../lib/platforms";

export default function RedditDashboard() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const platform = getPlatformById("reddit");

  const handleKeywordAdded = () => {
    // This will trigger the KeywordList to refresh via the onRefresh prop
  };

  if (!platform) return null;
  return (
    <PlatformDashboard
      platform={platform}
      stats={platform.defaultStats}
      isAddModalOpen={isAddModalOpen}
      onAddModalOpen={() => setIsAddModalOpen(true)}
      onAddModalClose={() => setIsAddModalOpen(false)}
      onKeywordAdded={handleKeywordAdded}
    />
  );
}
