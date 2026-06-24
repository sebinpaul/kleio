"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useApi, ApiUnauthorizedError } from "@/lib/api";

export default function SettingsPage() {
  const api = useApi();
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const settings = await api.getNotificationSettings();
      setEmailNotifications(settings.emailNotifications);
      setError(null);
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await api.updateNotificationSettings({ emailNotifications });
      setSaved(true);
    } catch (err) {
      if (err instanceof ApiUnauthorizedError) return;
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20">
      <div className="px-8 py-6 border-b border-slate-200/60 bg-white/60 backdrop-blur-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>
        <p className="text-sm text-slate-500 mt-0.5">Notification preferences</p>
      </div>

      <div className="px-8 py-8 max-w-xl">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
          {loading ? (
            <div className="h-20 bg-slate-100 rounded-lg animate-pulse" />
          ) : (
            <>
              {error && (
                <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
                  {error}
                </div>
              )}
              {saved && (
                <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
                  Settings saved.
                </div>
              )}

              <div>
                <h2 className="text-base font-semibold text-slate-900">Email notifications</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Master switch for mention alert emails. Per-keyword toggles in each keyword&apos;s settings still apply.
                </p>
                <label className="mt-4 flex items-center gap-3 cursor-pointer rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={emailNotifications}
                    onChange={(e) => setEmailNotifications(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm text-slate-700">Send email alerts for new mentions</span>
                </label>
              </div>

              <button
                onClick={handleSave}
                disabled={saving}
                className="gradient-button px-5 py-2.5 rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save settings"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
