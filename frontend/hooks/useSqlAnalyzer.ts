import { useState } from "react";
import { AnalyzeResponse } from "@/components/sql-analyzer/types";

interface UseSqlAnalyzerOptions {
  apiBase?: string;
}

const DEFAULT_SQL = `SELECT o.user_id, COUNT(*) AS cnt
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE LOWER(u.email) = LOWER('test@example.com')
GROUP BY o.user_id
ORDER BY cnt DESC;`;

const DEFAULT_SCHEMA = `-- Optional. Paste CREATE TABLEs or just key columns.
-- users(id PK, email)
-- orders(id PK, user_id FK -> users.id, created_at)`;

export function useSqlAnalyzer({ apiBase = "http://localhost:8000" }: UseSqlAnalyzerOptions = {}) {
  const [dialect, setDialect] = useState("postgres");
  const [sql, setSql] = useState(DEFAULT_SQL);
  const [schemaText, setSchemaText] = useState(DEFAULT_SCHEMA);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  async function analyze() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${apiBase}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dialect,
          sql,
          schema_text: schemaText?.trim() || null,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
      }

      const data = (await response.json()) as AnalyzeResponse;
      setResult(data);
    } catch (e: any) {
      setError(e?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setDialect("postgres");
    setSql(DEFAULT_SQL);
    setSchemaText(DEFAULT_SCHEMA);
    setError(null);
    setResult(null);
  }

  return {
    dialect,
    sql,
    schemaText,
    loading,
    error,
    result,
    setDialect,
    setSql,
    setSchemaText,
    analyze,
    reset,
  };
}
