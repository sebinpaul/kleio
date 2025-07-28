"use client";

import React, { useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { useApi, Keyword } from "@/lib/api";
import KeywordModal from "./KeywordModal";
import DeleteKeywordModal from "./DeleteKeywordModal";

type KeywordListProps = {
  platform?: string;
  onRefresh?: () => void;
};

export interface KeywordListRef {
  refresh: () => void;
}

const KeywordList = forwardRef<KeywordListRef, KeywordListProps>(({ platform, onRefresh }, ref) => {
  const api = useApi();
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingKeyword, setEditingKeyword] = useState<Keyword | undefined>(undefined);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deletingKeyword, setDeletingKeyword] = useState<Keyword | undefined>(undefined);
  const [isDeleting, setIsDeleting] = useState(false);

  const getPlatformIcon = (platformName: string) => {
    const platform = platformName.toLowerCase();
    
    if (platform === 'reddit') {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249z" />
        </svg>
      );
    }
    
    if (platform === 'hackernews') {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M0 24V0h24v24H0zM6.951 5.896l4.112 15.173L19.088 5.896h-2.288l-2.219 8.2-4.036-8.2h-2.288z" />
        </svg>
      );
    }
    
    if (platform === 'twitter') {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
        </svg>
      );
    }
    
    if (platform === 'linkedin') {
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
        </svg>
      );
    }
    
    return (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
      </svg>
    );
  };

  const getPlatformColor = (platformName: string) => {
    const platform = platformName.toLowerCase();
    switch (platform) {
      case 'reddit': return 'text-orange-600 bg-orange-100';
      case 'hackernews': return 'text-orange-700 bg-orange-100';
      case 'twitter': return 'text-blue-600 bg-blue-100';
      case 'linkedin': return 'text-blue-700 bg-blue-100';
      default: return 'text-indigo-600 bg-indigo-100';
    }
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
      await api.toggleKeyword(id);
      await loadKeywords();
      onRefresh?.();
    } catch (err) {
      console.error("Error toggling keyword:", err);
    }
  };

  const handleEdit = (keyword: Keyword) => {
    setEditingKeyword(keyword);
    setEditModalOpen(true);
  };

  const handleDelete = (keyword: Keyword) => {
    setDeletingKeyword(keyword);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!deletingKeyword) return;
    
    setIsDeleting(true);
    try {
      await api.deleteKeyword(deletingKeyword.id);
      await loadKeywords();
      onRefresh?.();
      setDeleteModalOpen(false);
      setDeletingKeyword(undefined);
    } catch (err) {
      console.error("Error deleting keyword:", err);
    } finally {
      setIsDeleting(false);
    }
  };

  useImperativeHandle(ref, () => ({
    refresh: loadKeywords,
  }));

  useEffect(() => {
    loadKeywords();
  }, [platform]);

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-4 animate-pulse">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-slate-200 rounded-lg"></div>
                <div>
                  <div className="w-32 h-4 bg-slate-200 rounded mb-2"></div>
                  <div className="w-24 h-3 bg-slate-200 rounded"></div>
                </div>
              </div>
              <div className="flex space-x-2">
                <div className="w-8 h-8 bg-slate-200 rounded-lg"></div>
                <div className="w-8 h-8 bg-slate-200 rounded-lg"></div>
                <div className="w-8 h-8 bg-slate-200 rounded-lg"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-2">Error Loading Keywords</h3>
        <p className="text-slate-600 mb-4">{error}</p>
        <button 
          onClick={loadKeywords}
          className="gradient-button px-4 py-2 rounded-lg text-sm font-medium"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (keywords.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-slate-900 mb-2">No Keywords Yet</h3>
        <p className="text-slate-600 mb-6 max-w-md mx-auto">
          Start monitoring mentions by adding your first keyword. Track what people are saying about your brand or any topic.
        </p>
        <button className="gradient-button px-6 py-3 rounded-xl font-medium">
          <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Your First Keyword
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {keywords.map((keyword) => (
        <div 
          key={keyword.id} 
          className="bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all duration-200 p-4"
        >
          <div className="flex items-center justify-between">
            {/* Left Side - Keyword Info */}
            <div className="flex items-center space-x-4 flex-1">
              {/* Platform Icon */}
              <div className={`p-2.5 rounded-lg ${getPlatformColor(keyword.platform)}`}>
                {getPlatformIcon(keyword.platform)}
              </div>
              
              {/* Keyword Details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-3 mb-1">
                  <h3 className="text-lg font-semibold text-slate-900 truncate">
                    {keyword.keyword}
                  </h3>
                  <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                    keyword.enabled 
                      ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' 
                      : 'bg-slate-100 text-slate-600 border border-slate-200'
                  }`}>
                    <div className={`w-1.5 h-1.5 rounded-full mr-2 ${
                      keyword.enabled ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
                    }`}></div>
                    {keyword.enabled ? 'Active' : 'Paused'}
                  </div>
                </div>
                
                {/* Platform & Settings Info */}
                <div className="flex items-center space-x-4 text-sm text-slate-500">
                  <span className="capitalize font-medium">
                    {platform === 'all' ? 'All Platforms' : keyword.platform}
                  </span>
                  <span>•</span>
                  <span>{keyword.matchMode || 'Contains'}</span>
                  {keyword.platformSpecificFilters && keyword.platformSpecificFilters.length > 0 && (
                    <>
                      <span>•</span>
                      <span>{keyword.platformSpecificFilters.length} filter(s)</span>
                    </>
                  )}
                  {keyword.caseSensitive && (
                    <>
                      <span>•</span>
                      <span className="text-amber-600 font-medium">Case Sensitive</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Right Side - Actions */}
            <div className="flex items-center space-x-2 ml-4">
              {/* Toggle Button */}
              <button
                onClick={() => handleToggle(keyword.id)}
                className={`p-2 rounded-lg transition-all duration-200 ${
                  keyword.enabled
                    ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200' 
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
                title={keyword.enabled ? 'Pause monitoring' : 'Resume monitoring'}
              >
                {keyword.enabled ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h.01M19 10a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </button>
              
              {/* Edit Button */}
              <button
                onClick={() => handleEdit(keyword)}
                className="p-2 rounded-lg bg-slate-100 text-slate-600 hover:bg-blue-100 hover:text-blue-700 transition-all duration-200"
                title="Edit keyword"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              
              {/* Delete Button */}
              <button
                onClick={() => handleDelete(keyword)}
                className="p-2 rounded-lg bg-slate-100 text-slate-600 hover:bg-red-100 hover:text-red-700 transition-all duration-200"
                title="Delete keyword"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      ))}

      {/* Edit Modal */}
      <KeywordModal
        isOpen={editModalOpen}
        onClose={() => {
          setEditModalOpen(false);
          setEditingKeyword(undefined);
        }}
        onKeywordSaved={() => {
          setEditModalOpen(false);
          setEditingKeyword(undefined);
          loadKeywords();
          onRefresh?.();
        }}
        platform={platform}
        keyword={editingKeyword}
      />

      {/* Delete Modal */}
      <DeleteKeywordModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setDeletingKeyword(undefined);
        }}
        onConfirm={handleDeleteConfirm}
        keyword={deletingKeyword}
        isLoading={isDeleting}
      />
    </div>
  );
});

KeywordList.displayName = "KeywordList";

export default KeywordList;
