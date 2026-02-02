import { AnalyzeResponse } from "./types";
import { Badge } from "../ui/Badge";
import { TabButton } from "../ui/TabButton";
import { ExplanationTab } from "./tabs/ExplanationTab";
import { IssuesTab } from "./tabs/IssuesTab";
import { OptimizationsTab } from "./tabs/OptimizationsTab";
import { RewriteTab } from "./tabs/RewriteTab";

interface ResultsPanelProps {
  result: AnalyzeResponse | null;
  apiBase: string;
  issueCounts: { info: number; warning: number; critical: number };
  activeTab: "explain" | "issues" | "opt" | "rewrite";
  onTabChange: (tab: "explain" | "issues" | "opt" | "rewrite") => void;
  onCopy: (text: string) => void;
}

export function ResultsPanel({
  result,
  apiBase,
  issueCounts,
  activeTab,
  onTabChange,
  onCopy,
}: ResultsPanelProps) {
  return (
    <div className="bg-slate-900 border border-white/10 rounded-2xl p-4 grid gap-3">
      <div className="flex gap-2.5 flex-wrap">
        <Badge>API: {apiBase}</Badge>
        <Badge>Confidence: {result?.confidence ?? "-"}</Badge>
        <Badge>Parsed: {result ? (result.parsed ? "yes" : "no") : "-"}</Badge>
        <Badge>
          Issues: {result ? `${issueCounts.critical} critical, ${issueCounts.warning} warn, ${issueCounts.info} info` : "-"}
        </Badge>
      </div>

      <div className="flex gap-2 flex-wrap">
        <TabButton active={activeTab === "explain"} onClick={() => onTabChange("explain")}>
          Explanation
        </TabButton>
        <TabButton active={activeTab === "issues"} onClick={() => onTabChange("issues")}>
          Issues
        </TabButton>
        <TabButton active={activeTab === "opt"} onClick={() => onTabChange("opt")}>
          Optimizations
        </TabButton>
        <TabButton active={activeTab === "rewrite"} onClick={() => onTabChange("rewrite")}>
          Rewritten SQL
        </TabButton>
      </div>

      <div className="h-px bg-white/10 my-3" />

      {!result && (
        <div className="text-xs opacity-90">
          Run analysis to see results.
        </div>
      )}

      {result && activeTab === "explain" && <ExplanationTab result={result} />}
      {result && activeTab === "issues" && <IssuesTab issues={result.issues} />}
      {result && activeTab === "opt" && <OptimizationsTab suggestions={result.suggestions} onCopy={onCopy} />}
      {result && activeTab === "rewrite" && <RewriteTab result={result} onCopy={onCopy} />}
    </div>
  );
}
