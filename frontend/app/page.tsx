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
    <div className="container">
      <h1 style={{ marginTop: 0 }}>SQL Explain + Optimize</h1>
      <p className="small">
        Paste a query → get explanation + issues + optimization suggestions + optional rewrite.
      </p>

      <div className="grid2">
        <div className="card row">
          <div>
            <label>Dialect</label>
            <select value={dialect} onChange={(e) => setDialect(e.target.value)}>
              <option value="postgres">Postgres</option>
              <option value="mysql">MySQL</option>
              <option value="sqlite">SQLite</option>
              <option value="tsql">SQL Server (T-SQL)</option>
              <option value="bigquery">BigQuery</option>
              <option value="snowflake">Snowflake</option>
            </select>
          </div>

          <div>
            <label>SQL</label>
            <textarea value={sql} onChange={(e) => setSql(e.target.value)} />
          </div>

          <div>
            <label>Schema (optional)</label>
            <textarea value={schemaText} onChange={(e) => setSchemaText(e.target.value)} />
          </div>

          <button onClick={analyze} disabled={loading || !sql.trim()}>
            {loading ? "Analyzing..." : "Analyze"}
          </button>

          {err && <div className="small" style={{ color: "#ff8b8b" }}>{err}</div>}
        </div>

        <div className="card row">
          <div className="kv">
            <span className="badge">API: {API_BASE}</span>
            <span className="badge">Confidence: {res?.confidence ?? "-"}</span>
            <span className="badge">Parsed: {res ? (res.parsed ? "yes" : "no") : "-"}</span>
            <span className="badge">Issues: {res ? `${issueCounts.critical} critical, ${issueCounts.warning} warn, ${issueCounts.info} info` : "-"}</span>
          </div>

          <div className="tabs">
            <button className={`tab ${tab === "explain" ? "tabActive" : ""}`} onClick={() => setTab("explain")}>
              Explanation
            </button>
            <button className={`tab ${tab === "issues" ? "tabActive" : ""}`} onClick={() => setTab("issues")}>
              Issues
            </button>
            <button className={`tab ${tab === "opt" ? "tabActive" : ""}`} onClick={() => setTab("opt")}>
              Optimizations
            </button>
            <button className={`tab ${tab === "rewrite" ? "tabActive" : ""}`} onClick={() => setTab("rewrite")}>
              Rewritten SQL
            </button>
          </div>

          <div className="hr" />

          {!res && (
            <div className="small">
              Run analysis to see results.
            </div>
          )}

          {res && tab === "explain" && (
            <div className="row">
              <div>
                <div className="small" style={{ marginBottom: 6 }}>Plain English</div>
                <pre>{res.explanation}</pre>
                <button onClick={() => copy(res.explanation)}>Copy explanation</button>
              </div>

              <div>
                <div className="small" style={{ marginBottom: 6 }}>Breakdown</div>
                <pre>{res.breakdown.map((b, i) => `${i + 1}. ${b}`).join("\n")}</pre>
              </div>

              <div>
                <div className="small" style={{ marginBottom: 6 }}>Assumptions</div>
                <pre>{(res.assumptions?.length ? res.assumptions : ["(none)"]).join("\n")}</pre>
              </div>

              <div>
                <div className="small" style={{ marginBottom: 6 }}>Parsed structure (debug)</div>
                <pre>{JSON.stringify(res.structure, null, 2)}</pre>
              </div>
            </div>
          )}

          {res && tab === "issues" && (
            <div className="row">
              {res.issues.length === 0 ? (
                <pre>No issues detected by static rules.</pre>
              ) : (
                res.issues.map((i, idx) => (
                  <div key={idx} className="card" style={{ background: "#0f1728" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                      <strong>{i.code}</strong>
                      <span className="badge">{i.severity}</span>
                    </div>
                    <div className="small" style={{ marginTop: 6 }}>{i.message}</div>
                    {i.evidence && <pre style={{ marginTop: 10 }}>{i.evidence}</pre>}
                  </div>
                ))
              )}
            </div>
          )}

          {res && tab === "opt" && (
            <div className="row">
              {res.suggestions.length === 0 ? (
                <pre>No suggestions returned.</pre>
              ) : (
                res.suggestions.map((s, idx) => (
                  <div key={idx} className="card" style={{ background: "#0f1728" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                      <strong>{s.title}</strong>
                      <span className="badge">impact: {s.impact}</span>
                    </div>

                    <div className="small" style={{ marginTop: 6 }}>{s.rationale}</div>

                    {s.actions?.length > 0 && (
                      <>
                        <div className="small" style={{ marginTop: 10 }}>Actions</div>
                        <pre>{s.actions.map((a, i) => `- ${a}`).join("\n")}</pre>
                      </>
                    )}

                    {s.index_sql?.length > 0 && (
                      <>
                        <div className="small" style={{ marginTop: 10 }}>Index SQL</div>
                        <pre>{s.index_sql.join("\n")}</pre>
                        <button onClick={() => copy(s.index_sql.join("\n"))}>Copy index SQL</button>
                      </>
                    )}

                    {s.rewrite_sql && (
                      <>
                        <div className="small" style={{ marginTop: 10 }}>Suggested rewrite</div>
                        <pre>{s.rewrite_sql}</pre>
                        <button onClick={() => copy(s.rewrite_sql!)}>Copy rewrite</button>
                      </>
                    )}

                    {s.caveats?.length > 0 && (
                      <>
                        <div className="small" style={{ marginTop: 10 }}>Caveats</div>
                        <pre>{s.caveats.map((c) => `- ${c}`).join("\n")}</pre>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {res && tab === "rewrite" && (
            <div className="row">
              <div>
                <div className="small" style={{ marginBottom: 6 }}>Rewritten SQL (top-level)</div>
                <pre>{res.rewritten_sql || "(no rewritten SQL returned)"}</pre>
                {res.rewritten_sql && (
                  <button onClick={() => copy(res.rewritten_sql!)}>Copy rewritten SQL</button>
                )}
              </div>

              <div>
                <div className="small" style={{ marginBottom: 6 }}>Normalized SQL (what the backend analyzed)</div>
                <pre>{res.normalized_sql}</pre>
                <button onClick={() => copy(res.normalized_sql)}>Copy normalized SQL</button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: 18 }} className="small">
        Tip: Add real performance grounding later by letting users paste EXPLAIN output and feeding it into the optimizer chain.
      </div>
    </div>
  );
}
