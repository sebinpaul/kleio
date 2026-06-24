"use client";

import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import Link from "next/link";
import {
  useApi,
  Keyword,
  KeywordAnalytics,
  KeywordAnalyticsRow,
  ApiUnauthorizedError,
} from "@/lib/api";
import { Platform, PlatformLabels, getMatchModeLabel } from "@/lib/enums";
import { platforms } from "@/lib/platforms";
import MentionSparkline from "./MentionSparkline";
import KeywordModal from "./KeywordModal";
import DeleteKeywordModal from "./DeleteKeywordModal";

type KeywordOverviewProps = {
  platform?: Platform;
  onAddKeyword?: () => void;
};

export interface KeywordOverviewRef {
  refresh: () => void;
}

function formatDate(iso: string | null): string {
  if (!iso) return "Never";
  return new Date(iso).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function TrendBadge({ trend }: { trend: KeywordAnalyticsRow["trend"] }) {
  if (trend === "up") {
    return <span className="text-xs font-medium text-emerald-600">↑ vs prior week</span>;
  }
  if (trend === "down") {
    return <span className="text-xs font-medium text-red-600">↓ vs prior week</span>;
  }
  return <span className="text-xs font-medium text-slate-400">→ flat</span>;
}

type WeekComparison = {
  trend: "up" | "down" | "flat";
  percent: number | null;
  delta: number;
};

function compareWeeks(current: number, prior: number): WeekComparison {
  const delta = current - prior;
  if (delta > 0) {
    const percent = prior > 0 ? Math.round((delta / prior) * 100) : null;
    return { trend: "up", percent, delta };
  }
  if (delta < 0) {
    const percent = prior > 0 ? Math.round((Math.abs(delta) / prior) * 100) : null;
    return { trend: "down", percent: percent !== null ? -percent : null, delta };
  }
  return { trend: "flat", percent: 0, delta: 0 };
}

function formatComparison({ trend, percent, delta }: WeekComparison): string {
  const arrow = trend === "up" ? "↑" : trend === "down" ? "↓" : "→";
  if (trend === "flat") return `${arrow} Same as prior week`;
  if (percent !== null) return `${arrow} ${Math.abs(percent)}% vs prior week`;
  const sign = delta > 0 ? "+" : "";
  return `${arrow} ${sign}${delta} vs prior week`;
}

function SummaryMetricCard({
  title,
  value,
  subtitle,
  comparison,
  accent,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  comparison: WeekComparison;
  accent: "indigo" | "violet" | "emerald" | "sky";
}) {
  const accentDot = {
    indigo: "bg-indigo-500",
    violet: "bg-violet-500",
    emerald: "bg-emerald-500",
    sky: "bg-sky-500",
  };

  const pillStyles = {
    up: "bg-emerald-50 text-emerald-700 border-emerald-200",
    down: "bg-red-50 text-red-700 border-red-200",
    flat: "bg-slate-50 text-slate-600 border-slate-200",
  };

  return (
    <div className="flex flex-col h-full rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-sm">
      <div className="flex items-center gap-2">
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${accentDot[accent]}`} />
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider leading-none">
          {title}
        </p>
      </div>

      <p className="text-2xl font-semibold text-slate-900 mt-3 tabular-nums leading-none">
        {value}
      </p>

      <p className="text-xs text-slate-500 mt-2 h-4 leading-4 truncate">
        {subtitle ?? "\u00A0"}
      </p>

      <div className="mt-auto pt-3">
        <span
          className={`inline-flex items-center px-2 py-1 rounded-md border text-[11px] font-medium leading-none ${pillStyles[comparison.trend]}`}
        >
          {formatComparison(comparison)}
        </span>
      </div>
    </div>
  );
}

const platformColors: Record<string, string> = {
  reddit: "bg-orange-100 text-orange-700",
  hackernews: "bg-orange-50 text-orange-800",
  twitter: "bg-blue-100 text-blue-700",
  youtube: "bg-red-100 text-red-700",
};

const KeywordOverview = forwardRef<KeywordOverviewRef, KeywordOverviewProps>(
  function KeywordOverview({ platform, onAddKeyword }, ref) {
    const api = useApi();
    const [data, setData] = useState<KeywordAnalytics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [editingKeyword, setEditingKeyword] = useState<Keyword | undefined>();
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [deletingKeyword, setDeletingKeyword] = useState<Keyword | undefined>();
    const [isDeleting, setIsDeleting] = useState(false);
    const loadInFlight = useRef(false);

    const load = useCallback(async () => {
      if (loadInFlight.current) return;
      loadInFlight.current = true;
      try {
        setLoading(true);
        const analytics = await api.getKeywordAnalytics(undefined, platform);
        setData(analytics);
        setError(null);
      } catch (err) {
        if (err instanceof ApiUnauthorizedError) return;
        setError(err instanceof Error ? err.message : "Failed to load overview");
      } finally {
        loadInFlight.current = false;
        setLoading(false);
      }
    }, [api, platform]);

    useImperativeHandle(ref, () => ({ refresh: load }), [load]);

    useEffect(() => {
      load();
    }, [load]);

    const handleToggle = async (row: Keyword) => {
      setActionError(null);
      try {
        await api.toggleKeyword(row.id, row.platform);
        await load();
      } catch (err) {
        if (err instanceof ApiUnauthorizedError) return;
        setActionError(err instanceof Error ? err.message : "Failed to update keyword");
      }
    };

    const handleEdit = (row: Keyword) => {
      setEditingKeyword(row);
      setEditModalOpen(true);
    };

    const handleDelete = (row: Keyword) => {
      setDeletingKeyword(row);
      setDeleteModalOpen(true);
    };

    const handleDeleteConfirm = async () => {
      if (!deletingKeyword) return;
      setIsDeleting(true);
      setActionError(null);
      try {
        await api.deleteKeyword(deletingKeyword.id, deletingKeyword.platform);
        setDeleteModalOpen(false);
        setDeletingKeyword(undefined);
        await load();
      } catch (err) {
        if (err instanceof ApiUnauthorizedError) return;
        setActionError(err instanceof Error ? err.message : "Failed to delete keyword");
      } finally {
        setIsDeleting(false);
      }
    };

    if (loading) {
      return (
        <div className="space-y-4 animate-pulse">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-[7.5rem] bg-slate-100 rounded-xl" />
            ))}
          </div>
          <div className="h-64 bg-slate-100 rounded-xl" />
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <button onClick={load} className="gradient-button px-4 py-2 rounded-lg text-sm">
            Try again
          </button>
        </div>
      );
    }

    if (!data || data.keywords.length === 0) {
      if (platform && onAddKeyword) {
        return (
          <div className="text-center py-16">
            <h3 className="text-xl font-semibold text-slate-900 mb-2">No keywords yet</h3>
            <p className="text-slate-600 mb-6 max-w-md mx-auto">
              Add your first {PlatformLabels[platform]} keyword to start tracking mentions.
            </p>
            <button
              onClick={onAddKeyword}
              className="gradient-button px-6 py-3 rounded-xl font-medium"
            >
              <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Your First Keyword
            </button>
          </div>
        );
      }

      return (
        <div className="text-center py-16">
          <h3 className="text-xl font-semibold text-slate-900 mb-2">No keywords yet</h3>
          <p className="text-slate-600 mb-6 max-w-md mx-auto">
            Pick a platform below to add your first keyword and start tracking mentions.
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {platforms.map((p) => (
              <Link
                key={p.id}
                href={`/dashboard/${p.id}`}
                className="gradient-button px-4 py-2 rounded-lg text-sm font-medium"
              >
                Add on {p.name}
              </Link>
            ))}
          </div>
        </div>
      );
    }

    const { summary } = data;
    const showPlatformColumn = !platform;

    const keywordsAddedLast7 = summary.keywordsAddedLast7Days ?? 0;
    const keywordsAddedPrior7 = summary.keywordsAddedPrior7Days ?? 0;
    const mentionsPrior7 = summary.mentionsPrior7Days ?? 0;
    const mentionsInWindow = summary.mentionsInWindow ?? 0;
    const mentionsPriorWindow = summary.mentionsPriorWindow ?? 0;

    const keywordsComparison = compareWeeks(keywordsAddedLast7, keywordsAddedPrior7);
    const mentionsVelocityComparison = compareWeeks(summary.mentionsLast7Days, mentionsPrior7);
    const last7Comparison = compareWeeks(summary.mentionsLast7Days, mentionsPrior7);
    const windowComparison = compareWeeks(mentionsInWindow, mentionsPriorWindow);

    return (
      <div className="space-y-6">
        {actionError && (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            {actionError}
          </div>
        )}

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 items-stretch">
          <SummaryMetricCard
            title="Keywords"
            value={summary.totalKeywords}
            subtitle={`${summary.activeKeywords} active`}
            comparison={keywordsComparison}
            accent="indigo"
          />
          <SummaryMetricCard
            title="All-time mentions"
            value={summary.totalMentions}
            subtitle={`${summary.mentionsLast7Days} this week`}
            comparison={mentionsVelocityComparison}
            accent="violet"
          />
          <SummaryMetricCard
            title="Last 7 days"
            value={summary.mentionsLast7Days}
            subtitle={`${mentionsPrior7} in prior week`}
            comparison={last7Comparison}
            accent="emerald"
          />
          <SummaryMetricCard
            title={`${summary.windowDays}d window`}
            value={mentionsInWindow}
            subtitle="mentions in chart period"
            comparison={windowComparison}
            accent="sky"
          />
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full min-w-[900px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Keyword</th>
                {showPlatformColumn && <th className="px-4 py-3">Platform</th>}
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Added</th>
                <th className="px-4 py-3">Last mention</th>
                <th className="px-4 py-3">Total</th>
                <th className="px-4 py-3">7d / trend</th>
                <th className="px-4 py-3">Activity</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.keywords.map((row) => (
                <tr key={row.id} className="bg-white hover:bg-slate-50/80">
                  <td className="px-4 py-3">
                    <p className="font-semibold text-slate-900">{row.keyword}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {getMatchModeLabel(row.matchMode)}
                      {row.caseSensitive ? " · case sensitive" : ""}
                    </p>
                  </td>
                  {showPlatformColumn && (
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                          platformColors[row.platform] || "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {PlatformLabels[row.platform as Platform] || row.platform}
                      </span>
                    </td>
                  )}
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                        row.enabled ? "text-emerald-700" : "text-slate-500"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          row.enabled ? "bg-emerald-500" : "bg-slate-400"
                        }`}
                      />
                      {row.enabled ? "Active" : "Paused"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                    {formatDate(row.createdAt)}
                  </td>
                  <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                    {formatDateTime(row.lastMentionAt)}
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {row.totalMentions > 0 ? (
                      <Link
                        href={`/dashboard/mentions?keywordId=${row.id}&keyword=${encodeURIComponent(row.keyword)}`}
                        className="text-indigo-600 hover:text-indigo-800 hover:underline"
                      >
                        {row.totalMentions}
                      </Link>
                    ) : (
                      row.totalMentions
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-slate-900">{row.mentionsLast7Days}</p>
                    <TrendBadge trend={row.trend} />
                  </td>
                  <td className="px-4 py-3">
                    <MentionSparkline data={row.timeline} />
                    <p className="text-[10px] text-slate-400 mt-1">
                      {row.mentionsInWindow} in {summary.windowDays}d
                    </p>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleToggle(row)}
                        className={`p-1.5 rounded-lg transition-colors ${
                          row.enabled
                            ? "text-emerald-700 hover:bg-emerald-50"
                            : "text-slate-500 hover:bg-slate-100"
                        }`}
                        title={row.enabled ? "Pause" : "Resume"}
                      >
                        {row.enabled ? (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        )}
                      </button>
                      <button
                        onClick={() => handleEdit(row)}
                        className="p-1.5 rounded-lg text-slate-500 hover:bg-blue-50 hover:text-blue-700"
                        title="Edit"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDelete(row)}
                        className="p-1.5 rounded-lg text-slate-500 hover:bg-red-50 hover:text-red-700"
                        title="Delete"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <KeywordModal
          isOpen={editModalOpen}
          onClose={() => {
            setEditModalOpen(false);
            setEditingKeyword(undefined);
          }}
          onKeywordSaved={() => {
            setEditModalOpen(false);
            setEditingKeyword(undefined);
            load();
          }}
          platform={editingKeyword?.platform ?? platform}
          keyword={editingKeyword}
        />

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
  }
);

export default KeywordOverview;
