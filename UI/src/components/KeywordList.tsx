"use client";

import React, { useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { useApi, Keyword } from "@/lib/api";
import { Platform, PlatformFilterLabels, MatchMode, ContentType, ContentTypeLabels } from "@/lib/enums";
import KeywordModal from "./KeywordModal";
import DeleteKeywordModal from "./DeleteKeywordModal";
import { Badge } from "@/components/ui/badge";

type KeywordListProps = {
  platform?: string;
  onRefresh?: () => void;
};

export interface KeywordListRef {
  refresh: () => void;
}

const KeywordList = forwardRef<KeywordListRef, KeywordListProps>(({ platform, onRefresh }, ref) => {
  // Component implementation
  const api = useApi();
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingKeyword, setEditingKeyword] = useState<Keyword | undefined>(undefined);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deletingKeyword, setDeletingKeyword] = useState<Keyword | undefined>(undefined);
  const [isDeleting, setIsDeleting] = useState(false);

  const getPlatformFilterLabel = (platform?: string) => {
    if (!platform) return "Filters";
    return PlatformFilterLabels[platform as Platform] || "Filters";
  };

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



  const handleDeleteClick = (keyword: Keyword) => {
    setDeletingKeyword(keyword);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!deletingKeyword) return;

    setIsDeleting(true);
    try {
      await api.deleteKeyword(deletingKeyword.id, platform);
      setKeywords((prev) => prev.filter((kw) => kw.id !== deletingKeyword.id));
      setDeleteModalOpen(false);
      setDeletingKeyword(undefined);
    } catch (err) {
      console.error("Error deleting keyword:", err);
      setError("Failed to delete keyword");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteClose = () => {
    setDeleteModalOpen(false);
    setDeletingKeyword(undefined);
    setIsDeleting(false);
  };

  const handleEdit = (keyword: Keyword) => {
    setEditingKeyword(keyword);
    setEditModalOpen(true);
  };

  const handleEditClose = () => {
    setEditModalOpen(false);
    setEditingKeyword(undefined);
  };

  // Expose refresh method to parent component
  useImperativeHandle(ref, () => ({
    refresh: loadKeywords
  }));

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
            <div className="space-y-1">
              <div>
                <span className="font-semibold text-gray-900">{kw.keyword}</span>
                {kw.platformSpecificFilters &&
                kw.platformSpecificFilters.length > 0 ? (
                  <span className="ml-2 text-xs text-gray-600">
                    ({getPlatformFilterLabel(platform)}:{" "}
                    {kw.platformSpecificFilters.join(", ")})
                  </span>
                ) : (
                  <span className="ml-2 text-xs text-gray-400">
                    (All {getPlatformFilterLabel(platform).toLowerCase()})
                  </span>
                )}
              </div>
              
              {/* Advanced Options Display */}
              {(kw.caseSensitive || kw.matchMode !== MatchMode.CONTAINS || (kw.contentTypes && kw.contentTypes.length !== 2)) && (
                <div className="flex flex-wrap gap-1">
                  {kw.caseSensitive && (
                    <Badge variant="secondary" className="text-xs">
                      Case Sensitive
                    </Badge>
                  )}
                  {kw.matchMode && kw.matchMode !== MatchMode.CONTAINS && (
                    <Badge variant="outline" className="text-xs">
                      {kw.matchMode.replace('_', ' ')}
                    </Badge>
                  )}
                  {kw.contentTypes && kw.contentTypes.length > 0 && (
                    <Badge variant="outline" className="text-xs">
                      {kw.contentTypes.map(ct => ContentTypeLabels[ct as ContentType]).join(', ')}
                    </Badge>
                  )}
                </div>
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
              <button 
                onClick={() => handleEdit(kw)}
                className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded hover:bg-yellow-200"
              >
                Edit
              </button>
              <button
                onClick={() => handleDeleteClick(kw)}
                className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded hover:bg-red-200"
              >
                Delete
              </button>
            </div>
          </div>
        ))
      )}
      
      <KeywordModal
        isOpen={editModalOpen}
        onClose={handleEditClose}
        onKeywordSaved={() => {
          loadKeywords();
          onRefresh?.();
        }}
        platform={platform}
        keyword={editingKeyword}
      />
      
      <DeleteKeywordModal
        isOpen={deleteModalOpen}
        onClose={handleDeleteClose}
        onConfirm={handleDeleteConfirm}
        keyword={deletingKeyword}
        isLoading={isDeleting}
      />
    </div>
  );
});

KeywordList.displayName = 'KeywordList';

export default KeywordList;
