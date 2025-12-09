"use client";

import { useState } from "react";
import PlatformDashboard from "../../../components/PlatformDashboard";
import { getPlatformById } from "../../../lib/platforms";

export default function QuoraDashboard() {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const platform = getPlatformById("quora");

  const handleKeywordAdded = () => {
    // refresh handled inside KeywordList
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


