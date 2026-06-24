"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useApi, Mention, ApiUnauthorizedError } from "@/lib/api";
import { Platform, PlatformLabels, SUPPORTED_LANGUAGES } from "@/lib/enums";

type MentionStatus = "active" | "unread" | "archived" | "all";

type MentionsFeedProps = {
  platform?: Platform;
  keywordId?: string;
  keywordLabel?: string;
  pageSize?: number;
  compact?: boolean;
  showFilters?: boolean;
  viewAllHref?: string;
};

const platformColors: Record<string, string> = {
  reddit: "bg-orange-100 text-orange-700",
  hackernews: "bg-orange-50 text-orange-800",
  twitter: "bg-blue-100 text-blue-700",
  youtube: "bg-red-100 text-red-700",
};

const contentTypeLabels: Record<string, string> = {
  post: "Post",
  comment: "Comment",
  title: "Title",
  body: "Body",
};

const STATUS_TABS: { id: MentionStatus; label: string }[] = [
  { id: "active", label: "Active" },
  { id: "unread", label: "Unread" },
  { id: "archived", label: "Archived" },
  { id: "all", label: "All" },
];

const languageLabels = new Map(SUPPORTED_LANGUAGES.map((l) => [l.code, l.label]));

function formatWhen(iso: string | null): string {
  if (!iso) return "Unknown time";
  const date = new Date(iso);
  const now = Date.now();
  const diffMs = now - date.getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function truncate(text: string, max: number): string {
  const trimmed = text.trim();
  if (trimmed.length <= max) return trimmed;
  return `${trimmed.slice(0, max - 1)}…`;
}

type MentionCardProps = {
  mention: Mention;
  showKeyword: boolean;
  compact?: boolean;
  onUpdate: (id: string, patch: Partial<Mention>) => void;
  updatingId: string | null;
};

function MentionCard({ mention, showKeyword, compact, onUpdate, updatingId }: MentionCardProps) {
  const headline = mention.title || truncate(mention.content, 120);
  const snippet = mention.title ? truncate(mention.content, 180) : "";
  const sourceLabel =
    mention.platform === "reddit" && mention.subreddit
      ? `r/${mention.subreddit}`
      : mention.author
        ? `@${mention.author.replace(/^@/, "")}`
        : PlatformLabels[mention.platform as Platform] || mention.platform;
  const langLabel = mention.detectedLanguage
    ? languageLabels.get(mention.detectedLanguage) || mention.detectedLanguage
    : null;
  const busy = updatingId === mention.id;

  return (
    <article
      className={`rounded-xl border bg-white p-4 transition-all ${
        mention.isArchived
          ? "border-slate-200 bg-slate-50/80 opacity-75"
          : mention.isRead
            ? "border-slate-200 hover:border-slate-300 hover:shadow-sm"
            : "border-indigo-200 bg-indigo-50/30 hover:border-indigo-300 hover:shadow-sm"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            {!mention.isRead && !mention.isArchived && (
              <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-600 text-white">
                New
              </span>
            )}
            <span
              className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                platformColors[mention.platform] || "bg-slate-100 text-slate-700"
              }`}
            >
              {PlatformLabels[mention.platform as Platform] || mention.platform}
            </span>
            {showKeyword && mention.keyword && (
              <span className="text-xs font-medium text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full">
                {mention.keyword}
              </span>
            )}
            <span className="text-xs text-slate-500">
              {contentTypeLabels[mention.contentType] || mention.contentType}
            </span>
            {langLabel && (
              <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                {langLabel}
              </span>
            )}
            {mention.platformScore != null && (
              <span className="text-xs text-slate-500">↑ {mention.platformScore}</span>
            )}
          </div>

          <h3 className={`font-semibold text-slate-900 leading-snug ${!mention.isRead ? "" : "font-medium"}`}>
            <a
              href={mention.sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-indigo-700"
              onClick={() => {
                if (!mention.isRead) onUpdate(mention.id, { isRead: true });
              }}
            >
              {headline}
            </a>
          </h3>

          {snippet && <p className="text-sm text-slate-600 mt-1.5 line-clamp-2">{snippet}</p>}

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs text-slate-500">
            <span>{sourceLabel}</span>
            <span>·</span>
            <span>Found {formatWhen(mention.discoveredAt)}</span>
            {mention.matchedText && (
              <>
                <span>·</span>
                <span>
                  Matched: <span className="font-medium text-slate-700">{mention.matchedText}</span>
                </span>
              </>
            )}
          </div>
        </div>

        <div className="shrink-0 flex flex-col gap-1">
          <a
            href={mention.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50"
            title="Open source"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
          {!compact && (
            <>
              {!mention.isRead && (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onUpdate(mention.id, { isRead: true })}
                  className="p-2 rounded-lg text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 disabled:opacity-50"
                  title="Mark as read"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </button>
              )}
              {!mention.isArchived ? (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onUpdate(mention.id, { isArchived: true, isRead: true })}
                  className="p-2 rounded-lg text-slate-400 hover:text-amber-600 hover:bg-amber-50 disabled:opacity-50"
                  title="Archive"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                  </svg>
                </button>
              ) : (
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onUpdate(mention.id, { isArchived: false })}
                  className="p-2 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 disabled:opacity-50"
                  title="Unarchive"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                  </svg>
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </article>
  );
}

export default function MentionsFeed({
  platform,
  keywordId,
  keywordLabel,
  pageSize = 20,
  compact = false,
  showFilters = false,
  viewAllHref,
}: MentionsFeedProps) {
  const api = useApi();
  const [mentions, setMentions] = useState<Mention[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<MentionStatus>("active");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const loadInFlight = useRef(false);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const load = useCallback(
    async (offset = 0, append = false) => {
      if (loadInFlight.current) return;
      loadInFlight.current = true;
      try {
        if (append) setLoadingMore(true);
        else setLoading(true);

        const limit = compact ? Math.min(pageSize, 10) : pageSize;
        const data = await api.getMentions({
          platform,
          keywordId,
          limit,
          offset,
          q: debouncedSearch || undefined,
          status: showFilters ? status : "active",
        });

        setMentions((prev) => (append ? [...prev, ...data.mentions] : data.mentions));
        setTotal(data.total);
        setError(null);
      } catch (err) {
        if (err instanceof ApiUnauthorizedError) return;
        setError(err instanceof Error ? err.message : "Failed to load mentions");
      } finally {
        loadInFlight.current = false;
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [api, platform, keywordId, pageSize, compact, debouncedSearch, status, showFilters]
  );

  useEffect(() => {
    load(0, false);
  }, [load]);

  const handleUpdate = async (id: string, patch: Partial<Mention>) => {
    setUpdatingId(id);
    try {
      const updated = await api.updateMention(id, {
        isRead: patch.isRead,
        isArchived: patch.isArchived,
      });
      setMentions((prev) => {
        const next = prev.map((m) => (m.id === id ? { ...m, ...updated } : m));
        if (showFilters && status === "active" && updated.isArchived) {
          return next.filter((m) => m.id !== id);
        }
        if (showFilters && status === "unread" && updated.isRead) {
          return next.filter((m) => m.id !== id);
        }
        if (showFilters && status === "archived" && !updated.isArchived) {
          return next.filter((m) => m.id !== id);
        }
        return next;
      });
      if (showFilters) setTotal((t) => Math.max(0, t - (patch.isArchived && status === "active" ? 1 : 0)));
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      setError(err instanceof Error ? err.message : "Failed to update mention");
    } finally {
      setUpdatingId(null);
    }
  };

  const hasMore = mentions.length < total;

  if (loading) {
    return (
      <div className="space-y-3 animate-pulse">
        {showFilters && <div className="h-10 bg-slate-100 rounded-lg" />}
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-slate-100 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showFilters && (
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 pb-1">
          <div className="flex flex-wrap gap-1 rounded-lg border border-slate-200 bg-slate-50 p-1">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setStatus(tab.id)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  status === tab.id
                    ? "bg-white text-indigo-700 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search title or content…"
            className="flex-1 h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400"
          />
        </div>
      )}

      {error && (
        <div className="text-center py-4">
          <p className="text-red-600 mb-3">{error}</p>
          <button onClick={() => load(0, false)} className="gradient-button px-4 py-2 rounded-lg text-sm">
            Try again
          </button>
        </div>
      )}

      {!error && mentions.length === 0 && (
        <div className="text-center py-12 text-slate-600">
          <p className="font-medium text-slate-900 mb-1">No mentions found</p>
          <p className="text-sm">
            {debouncedSearch
              ? `No results for "${debouncedSearch}".`
              : keywordLabel
                ? `Nothing found for "${keywordLabel}" yet.`
                : status === "archived"
                  ? "No archived mentions."
                  : status === "unread"
                    ? "You're all caught up — no unread mentions."
                    : "Matches will show up here when your keywords are mentioned."}
          </p>
        </div>
      )}

      {!error && mentions.length > 0 && (
        <>
          {(keywordLabel || platform) && (
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-slate-500">Showing</span>
              {keywordLabel && (
                <span className="font-medium text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full">
                  {keywordLabel}
                </span>
              )}
              {platform && (
                <span className="font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full capitalize">
                  {PlatformLabels[platform]}
                </span>
              )}
              <span className="text-slate-500">· {total} total</span>
            </div>
          )}

          <div className="space-y-3">
            {mentions.map((mention) => (
              <MentionCard
                key={mention.id}
                mention={mention}
                showKeyword={!keywordId}
                compact={compact}
                onUpdate={handleUpdate}
                updatingId={updatingId}
              />
            ))}
          </div>

          <div className="flex items-center justify-between pt-1">
            <p className="text-xs text-slate-500">
              {mentions.length} of {total} mentions
            </p>
            <div className="flex items-center gap-2">
              {viewAllHref && compact && total > mentions.length && (
                <Link href={viewAllHref} className="text-sm font-medium text-indigo-600 hover:text-indigo-800">
                  View all
                </Link>
              )}
              {!compact && hasMore && (
                <button
                  onClick={() => load(mentions.length, true)}
                  disabled={loadingMore}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-800 disabled:opacity-50"
                >
                  {loadingMore ? "Loading…" : "Load more"}
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
