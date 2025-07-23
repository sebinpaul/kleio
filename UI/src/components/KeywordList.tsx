"use client";

import React, { useEffect, useState } from "react";
import { useApi, Keyword } from "@/lib/api";

type KeywordListProps = {
  platform?: string;
  // ...other props
};

export default function KeywordList({ platform }: KeywordListProps) {
  const api = useApi();
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadKeywords = async () => {
    try {
      setLoading(true);
      const data = await api.getUserKeywords(platform);
      setKeywords(data);
      setError(null);
    } catch (err) {
      console.error("Error loading keywords:", err);
      setError("Failed to load keywords");
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (id: string) => {
    try {
      const updatedKeyword = await api.toggleKeyword(id, platform);
      setKeywords((prev) =>
        prev.map((kw) => (kw.id === id ? updatedKeyword : kw))
      );
    } catch (err) {
      console.error("Error toggling keyword:", err);
      setError("Failed to toggle keyword");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this keyword?")) {
      return;
    }

    try {
      await api.deleteKeyword(id, platform);
      setKeywords((prev) => prev.filter((kw) => kw.id !== id));
    } catch (err) {
      console.error("Error deleting keyword:", err);
      setError("Failed to delete keyword");
    }
  };

  useEffect(() => {
    loadKeywords();
  }, [platform]);

  if (loading) {
    return <div className="text-gray-500">Loading keywords...</div>;
  }

  if (error) {
    return (
      <div className="text-red-500">
        {error}
        <button
          onClick={loadKeywords}
          className="ml-2 text-blue-500 hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {keywords.length === 0 ? (
        <div className="text-gray-500">No keywords added yet.</div>
      ) : (
        keywords.map((kw) => (
          <div
            key={kw.id}
            className="flex flex-col sm:flex-row sm:items-center justify-between border rounded p-3 bg-gray-50"
          >
            <div>
              <span className="font-semibold text-gray-900">{kw.keyword}</span>
              {kw.platformSpecificFilters &&
              kw.platformSpecificFilters.length > 0 ? (
                <span className="ml-2 text-xs text-gray-600">
                  ({platform === "reddit" ? "Subreddits" : "Filters"}:{" "}
                  {kw.platformSpecificFilters.join(", ")})
                </span>
              ) : (
                <span className="ml-2 text-xs text-gray-400">
                  (All {platform === "reddit" ? "subreddits" : "sources"})
                </span>
              )}
            </div>
            <div className="flex gap-2 mt-2 sm:mt-0">
              <button
                onClick={() => handleToggle(kw.id)}
                className={`px-2 py-1 rounded text-xs font-medium ${
                  kw.enabled
                    ? "bg-green-100 text-green-700 hover:bg-green-200"
                    : "bg-gray-200 text-gray-500 hover:bg-gray-300"
                }`}
              >
                {kw.enabled ? "Enabled" : "Disabled"}
              </button>
              <button className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200">
                Edit
              </button>
              <button
                onClick={() => handleDelete(kw.id)}
                className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
              >
                Delete
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
