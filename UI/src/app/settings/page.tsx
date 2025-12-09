"use client";

import { useEffect, useState } from "react";
import { useApi } from "@/lib/api";

export default function SettingsPage() {
  const { listProxies, createProxy, deleteProxy, uploadProxiesCsv, getPlatformSources, putPlatformSources } = useApi() as any;
  const [proxies, setProxies] = useState<any[]>([]);
  const [newProxy, setNewProxy] = useState("");
  const [csvText, setCsvText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Platform sources state
  const [liSources, setLiSources] = useState("");
  const [fbSources, setFbSources] = useState("");
  const [fbToken, setFbToken] = useState("");
  const [quoraSources, setQuoraSources] = useState("");

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listProxies();
      setProxies(items);
    } catch (e: any) {
      setError(e.message || "Failed to load proxies");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // load platform sources
    (async () => {
      try {
        const li = await getPlatformSources("linkedin");
        setLiSources((li.sources || []).join("\n"));
      } catch {}
      try {
        const fb = await getPlatformSources("facebook");
        setFbSources((fb.sources || []).join("\n"));
        const cfg = fb.config || {};
        setFbToken((cfg.app_token as string) || "");
      } catch {}
      try {
        const qo = await getPlatformSources("quora");
        setQuoraSources((qo.sources || []).join("\n"));
      } catch {}
    })();
  }, []);

  const onAdd = async () => {
    if (!newProxy.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await createProxy(newProxy.trim());
      setNewProxy("");
      await refresh();
    } catch (e: any) {
      setError(e.message || "Failed to add proxy");
    } finally {
      setLoading(false);
    }
  };

  const onDelete = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await deleteProxy(id);
      await refresh();
    } catch (e: any) {
      setError(e.message || "Failed to delete proxy");
    } finally {
      setLoading(false);
    }
  };

  const onUploadCsv = async () => {
    if (!csvText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await uploadProxiesCsv(csvText);
      setCsvText("");
      await refresh();
    } catch (e: any) {
      setError(e.message || "Failed to upload proxies");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Proxies</h2>
        <p className="text-slate-600 text-sm">Manage HTTP/SOCKS proxies used by Reddit, Hacker News, and Twitter scrapers.</p>

        {error && (
          <div className="p-3 rounded bg-red-50 text-red-700 text-sm">{error}</div>
        )}

        <div className="flex items-center space-x-2">
          <input
            className="flex-1 border rounded px-3 py-2"
            placeholder="http://user:pass@host:port or socks5://host:1080"
            value={newProxy}
            onChange={(e) => setNewProxy(e.target.value)}
          />
          <button
            onClick={onAdd}
            disabled={loading}
            className="px-4 py-2 rounded bg-indigo-600 text-white disabled:opacity-50"
          >
            Add
          </button>
        </div>

        <div className="grid grid-cols-1 gap-2">
          {proxies.map((p) => (
            <div key={p.id} className="flex items-center justify-between p-3 border rounded">
              <div>
                <div className="font-mono text-sm">{p.url}</div>
                <div className="text-xs text-slate-500">active: {String(p.is_active)} {p.cooldown_until ? `(cooldown until ${p.cooldown_until})` : ""}</div>
              </div>
              <button
                onClick={() => onDelete(p.id)}
                className="px-3 py-1.5 rounded bg-red-600 text-white text-sm"
                disabled={loading}
              >
                Delete
              </button>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">Bulk upload (CSV / plain text)</h3>
          <textarea
            className="w-full border rounded p-2 h-32 font-mono text-sm"
            placeholder={"http://user:pass@host:port\nsocks5://host:1080"}
            value={csvText}
            onChange={(e) => setCsvText(e.target.value)}
          />
          <button
            onClick={onUploadCsv}
            disabled={loading}
            className="px-4 py-2 rounded bg-slate-700 text-white disabled:opacity-50"
          >
            Upload
          </button>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">LinkedIn sources</h2>
        <p className="text-slate-600 text-sm">One per line. Accepts full URLs or prefixes like hashtag:ai, company:microsoft, profile:satyanadella</p>
        <textarea className="w-full border rounded p-2 h-32 font-mono text-sm" value={liSources} onChange={(e)=>setLiSources(e.target.value)} />
        <button
          onClick={async ()=>{ setLoading(true); setError(null); try { await putPlatformSources("linkedin", { sources: liSources.split(/\n+/).map(s=>s.trim()).filter(Boolean) }); } catch(e:any){ setError(e.message||"Failed to save"); } finally { setLoading(false);} }}
          disabled={loading}
          className="px-4 py-2 rounded bg-slate-700 text-white disabled:opacity-50"
        >Save LinkedIn</button>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Facebook Pages</h2>
        <p className="text-slate-600 text-sm">One per line. Accepts page:cnn, usernames, or full URLs. Optional App Token to use Graph API.</p>
        <textarea className="w-full border rounded p-2 h-32 font-mono text-sm" value={fbSources} onChange={(e)=>setFbSources(e.target.value)} />
        <input className="w-full border rounded p-2 font-mono text-sm" placeholder="Facebook App Access Token (optional)" value={fbToken} onChange={(e)=>setFbToken(e.target.value)} />
        <button
          onClick={async ()=>{ setLoading(true); setError(null); try { await putPlatformSources("facebook", { sources: fbSources.split(/\n+/).map(s=>s.trim()).filter(Boolean), config: fbToken? { app_token: fbToken }: {} }); } catch(e:any){ setError(e.message||"Failed to save"); } finally { setLoading(false);} }}
          disabled={loading}
          className="px-4 py-2 rounded bg-slate-700 text-white disabled:opacity-50"
        >Save Facebook</button>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Quora topics</h2>
        <p className="text-slate-600 text-sm">One per line. Topic URLs like https://www.quora.com/topic/Artificial-Intelligence</p>
        <textarea className="w-full border rounded p-2 h-32 font-mono text-sm" value={quoraSources} onChange={(e)=>setQuoraSources(e.target.value)} />
        <button
          onClick={async ()=>{ setLoading(true); setError(null); try { await putPlatformSources("quora", { sources: quoraSources.split(/\n+/).map(s=>s.trim()).filter(Boolean) }); } catch(e:any){ setError(e.message||"Failed to save"); } finally { setLoading(false);} }}
          disabled={loading}
          className="px-4 py-2 rounded bg-slate-700 text-white disabled:opacity-50"
        >Save Quora</button>
      </section>
    </div>
  );
}