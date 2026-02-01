"use client";

import { useMemo, useState } from "react";

type Issue = {
  code: string;
  severity: "info" | "warning" | "critical";
  message: string;
  evidence?: string | null;
};

type Suggestion = {
  title: string;
  impact: "low" | "medium" | "high";
  rationale: string;
  actions: string[];
  index_sql: string[];
  rewrite_sql?: string | null;
  caveats: string[];
};

type AnalyzeResponse = {
  dialect: string;
  normalized_sql: string;
  parsed: boolean;
  structure: any;
  explanation: string;
  breakdown: string[];
  assumptions: string[];
  issues: Issue[];
  suggestions: Suggestion[];
  rewritten_sql?: string | null;
  confidence: "low" | "medium" | "high";
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function Page() {
  const [dialect, setDialect] = useState("postgres");
  const [sql, setSql] = useState(
`SELECT o.user_id, COUNT(*) AS cnt
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE LOWER(u.email) = LOWER('test@example.com')
GROUP BY o.user_id
ORDER BY cnt DESC;`
  );
  const [schemaText, setSchemaText] = useState(
`-- Optional. Paste CREATE TABLEs or just key columns.
-- users(id PK, email)
-- orders(id PK, user_id FK -> users.id, created_at)`
  );

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [res, setRes] = useState<AnalyzeResponse | null>(null);

  const [tab, setTab] = useState<"explain" | "issues" | "opt" | "rewrite">("explain");

  const issueCounts = useMemo(() => {
    const counts = { info: 0, warning: 0, critical: 0 };
    if (!res) return counts;
    res.issues.forEach(i => counts[i.severity]++);
    return counts;
  }, [res]);

  async function analyze() {
    setLoading(true);
    setErr(null);
    setRes(null);

    try {
      const r = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dialect, sql, schema_text: schemaText?.trim() || null }),
      });

      if (!r.ok) {
        const t = await r.text();
        throw new Error(t || `HTTP ${r.status}`);
      }
      const data = (await r.json()) as AnalyzeResponse;
      setRes(data);
      setTab("explain");
    } catch (e: any) {
      setErr(e?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function copy(text: string) {
    navigator.clipboard.writeText(text);
  }

  return (
    <div className="max-w-7xl mx-auto px-7 py-7 md:px-7">
      <h1 className="mt-0 text-3xl font-bold">SQL Explain + Optimize</h1>
      <p className="text-xs opacity-90 mb-3">
        Paste a query → get explanation + issues + optimization suggestions + optional rewrite.
      </p>

      <div className="grid gap-3 lg:grid-cols-2 items-start">
        <div className="bg-slate-900 border border-white/10 rounded-2xl p-4 grid gap-3">
          <div>
            <label className="block text-xs opacity-90 mb-1.5">Dialect</label>
            <select value={dialect} onChange={(e) => setDialect(e.target.value)} className="w-full bg-slate-950 text-slate-100 border border-white/10 rounded-lg px-2.5 py-2.5 outline-none">
              <option value="postgres">Postgres</option>
              <option value="mysql">MySQL</option>
              <option value="sqlite">SQLite</option>
              <option value="tsql">SQL Server (T-SQL)</option>
              <option value="bigquery">BigQuery</option>
              <option value="snowflake">Snowflake</option>
            </select>
          </div>

          <div>
            <label className="block text-xs opacity-90 mb-1.5">SQL</label>
            <textarea value={sql} onChange={(e) => setSql(e.target.value)} className="w-full min-h-44 bg-slate-950 text-slate-100 border border-white/10 rounded-lg px-2.5 py-2.5 outline-none font-mono text-sm resize-y" />
          </div>

          <div>
            <label className="block text-xs opacity-90 mb-1.5">Schema (optional)</label>
            <textarea value={schemaText} onChange={(e) => setSchemaText(e.target.value)} className="w-full min-h-44 bg-slate-950 text-slate-100 border border-white/10 rounded-lg px-2.5 py-2.5 outline-none font-mono text-sm resize-y" />
          </div>

          <button onClick={analyze} disabled={loading || !sql.trim()} className="bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white px-3 py-2.5 rounded-lg font-semibold">
            {loading ? "Analyzing..." : "Analyze"}
          </button>

          {err && <div className="text-xs opacity-90 text-red-400">{err}</div>}
        </div>

        <div className="bg-slate-900 border border-white/10 rounded-2xl p-4 grid gap-3">
          <div className="flex gap-2.5 flex-wrap">
            <span className="text-xs px-2 py-1 rounded-full border border-white/10 whitespace-nowrap">API: {API_BASE}</span>
            <span className="text-xs px-2 py-1 rounded-full border border-white/10 whitespace-nowrap">Confidence: {res?.confidence ?? "-"}</span>
            <span className="text-xs px-2 py-1 rounded-full border border-white/10 whitespace-nowrap">Parsed: {res ? (res.parsed ? "yes" : "no") : "-"}</span>
            <span className="text-xs px-2 py-1 rounded-full border border-white/10 whitespace-nowrap">Issues: {res ? `${issueCounts.critical} critical, ${issueCounts.warning} warn, ${issueCounts.info} info` : "-"}</span>
          </div>

          <div className="flex gap-2 flex-wrap">
            <button className={`bg-transparent border ${tab === "explain" ? "bg-blue-600/25 border-blue-600/60" : "border-white/10"} text-slate-100 px-2.5 py-2 rounded-full cursor-pointer text-xs whitespace-nowrap`} onClick={() => setTab("explain")}>
              Explanation
            </button>
            <button className={`bg-transparent border ${tab === "issues" ? "bg-blue-600/25 border-blue-600/60" : "border-white/10"} text-slate-100 px-2.5 py-2 rounded-full cursor-pointer text-xs whitespace-nowrap`} onClick={() => setTab("issues")}>
              Issues
            </button>
            <button className={`bg-transparent border ${tab === "opt" ? "bg-blue-600/25 border-blue-600/60" : "border-white/10"} text-slate-100 px-2.5 py-2 rounded-full cursor-pointer text-xs whitespace-nowrap`} onClick={() => setTab("opt")}>
              Optimizations
            </button>
            <button className={`bg-transparent border ${tab === "rewrite" ? "bg-blue-600/25 border-blue-600/60" : "border-white/10"} text-slate-100 px-2.5 py-2 rounded-full cursor-pointer text-xs whitespace-nowrap`} onClick={() => setTab("rewrite")}>
              Rewritten SQL
            </button>
          </div>

          <div className="h-px bg-white/10 my-3" />

          {!res && (
            <div className="text-xs opacity-90">
              Run analysis to see results.
            </div>
          )}

          {res && tab === "explain" && (
            <div className="grid gap-3">
              <div>
                <div className="text-xs opacity-90 mb-1.5">Summary</div>
                <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{res.explanation}</pre>
                {/* <button onClick={() => copy(res.explanation)} className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm">Copy explanation</button> */}
              </div>

              <div>
                <div className="text-xs opacity-90 mb-1.5">Breakdown</div>
                <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{res.breakdown.map((b, i) => `${i + 1}. ${b}`).join("\n")}</pre>
              </div>

              <div>
                <div className="text-xs opacity-90 mb-1.5">Assumptions</div>
                <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{(res.assumptions?.length ? res.assumptions : ["(none)"]).join("\n")}</pre>
              </div>

              <div>
                <div className="text-xs opacity-90 mb-1.5">Parsed structure (debug)</div>
                <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{JSON.stringify(res.structure, null, 2)}</pre>
              </div>
            </div>
          )}

          {res && tab === "issues" && (
            <div className="grid gap-3">
              {res.issues.length === 0 ? (
                <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">No issues detected by static rules.</pre>
              ) : (
                res.issues.map((i, idx) => (
                  <div key={idx} className="bg-slate-800 border border-white/10 rounded-2xl p-4">
                    <div className="flex justify-between gap-2">
                      <strong>{i.code}</strong>
                      <span className="text-xs px-2 py-1 rounded-full border border-white/10 whitespace-nowrap">{i.severity}</span>
                    </div>
                    <div className="text-xs opacity-90 mt-1.5">{i.message}</div>
                    {i.evidence && <pre className="mt-2.5 whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{i.evidence}</pre>}
                  </div>
                ))
              )}
            </div>
          )}

          {res && tab === "opt" && (
            <div className="grid gap-3">
              {res.suggestions.length === 0 ? (
                <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">No suggestions returned.</pre>
              ) : (
                res.suggestions.map((s, idx) => (
                  <div key={idx} className="bg-slate-800 border border-white/10 rounded-2xl p-4">
                    <div className="flex justify-between gap-2">
                      <strong>{s.title}</strong>
                      <span className="text-xs px-2 py-1 rounded-full border border-white/10 whitespace-nowrap">impact: {s.impact}</span>
                    </div>

                    <div className="text-xs opacity-90 mt-1.5">{s.rationale}</div>

                    {s.actions?.length > 0 && (
                      <>
                        <div className="text-xs opacity-90 mt-2.5">Actions</div>
                        <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{s.actions.map((a, i) => `- ${a}`).join("\n")}</pre>
                      </>
                    )}

                    {s.index_sql?.length > 0 && (
                      <>
                        <div className="text-xs opacity-90 mt-2.5">Index SQL</div>
                        <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{s.index_sql.join("\n")}</pre>
                        <button onClick={() => copy(s.index_sql.join("\n"))} className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm">Copy index SQL</button>
                      </>
                    )}

                    {s.rewrite_sql && (
                      <>
                        <div className="text-xs opacity-90 mt-2.5">Suggested rewrite</div>
                        <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{s.rewrite_sql}</pre>
                        <button onClick={() => copy(s.rewrite_sql!)} className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm">Copy rewrite</button>
                      </>
                    )}

                    {s.caveats?.length > 0 && (
                      <>
                        <div className="text-xs opacity-90 mt-2.5">Caveats</div>
                        <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{s.caveats.map((c) => `- ${c}`).join("\n")}</pre>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {res && tab === "rewrite" && (
            <div className="grid gap-3">
              <div>
                <div className="text-xs opacity-90 mb-1.5">Rewritten SQL (top-level)</div>
                <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{res.rewritten_sql || "(no rewritten SQL returned)"}</pre>
                {res.rewritten_sql && (
                  <button onClick={() => copy(res.rewritten_sql!)} className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm">Copy rewritten SQL</button>
                )}
              </div>

              <div>
                <div className="text-xs opacity-90 mb-1.5">Normalized SQL (what the backend analyzed)</div>
                <pre className="whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0">{res.normalized_sql}</pre>
                <button onClick={() => copy(res.normalized_sql)} className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm">Copy normalized SQL</button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 text-xs opacity-90">
        Tip: Add real performance grounding later by letting users paste EXPLAIN output and feeding it into the optimizer chain.
      </div>
    </div>
  );
}
