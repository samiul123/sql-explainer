import { useMemo, useState, useEffect } from "react";
import { AnalyzeResponse } from "@/components/sql-analyzer/types";

interface UseAnalysisResultsOptions {
  result: AnalyzeResponse | null;
}

export function useAnalysisResults({ result }: UseAnalysisResultsOptions) {
  const [activeTab, setActiveTab] = useState<"explain" | "issues" | "opt" | "rewrite">("explain");

  const issueCounts = useMemo(() => {
    const counts = { info: 0, warning: 0, critical: 0 };
    if (!result) return counts;
    result.issues.forEach((issue) => counts[issue.severity]++);
    return counts;
  }, [result]);

  // Reset to explanation tab when new results arrive
  useEffect(() => {
    if (result) {
      setActiveTab("explain");
    }
  }, [result]);

  return {
    activeTab,
    setActiveTab,
    issueCounts,
  };
}
