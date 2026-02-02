"use client";

import { useSqlAnalyzer } from "@/hooks/useSqlAnalyzer";
import { useAnalysisResults } from "@/hooks/useAnalysisResults";
import { useClipboard } from "@/hooks/useClipboard";
import { InputPanel } from "@/components/sql-analyzer/InputPanel";
import { ResultsPanel } from "@/components/sql-analyzer/ResultsPanel";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function Page() {
  const {
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
  } = useSqlAnalyzer({ apiBase: API_BASE });

  const { activeTab, setActiveTab, issueCounts } = useAnalysisResults({ result });
  const { copy } = useClipboard();

  return (
    <div className="max-w-7xl mx-auto px-7 py-7 md:px-7">
      <h1 className="mt-0 text-3xl font-bold">SQL Explain + Optimize</h1>
      <p className="text-xs opacity-90 mb-3">
        Paste a query → get explanation + issues + optimization suggestions + optional rewrite.
      </p>

      <div className="grid gap-3 lg:grid-cols-2 items-start">
        <InputPanel
          dialect={dialect}
          sql={sql}
          schemaText={schemaText}
          loading={loading}
          error={error}
          onDialectChange={setDialect}
          onSqlChange={setSql}
          onSchemaChange={setSchemaText}
          onAnalyze={analyze}
        />

        <ResultsPanel
          result={result}
          apiBase={API_BASE}
          issueCounts={issueCounts}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          onCopy={copy}
        />
      </div>

      <div className="mt-4 text-xs opacity-90">
        Tip: Add real performance grounding later by letting users paste EXPLAIN output and feeding it into the optimizer chain.
      </div>
    </div>
  );
}
