import { Issue } from "../types";
import { Badge } from "../../ui/Badge";
import { CodeBlock } from "../../ui/CodeBlock";

interface IssueCardProps {
  issue: Issue;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-500/20 border-red-500/50 text-red-300",
  warning: "bg-yellow-500/20 border-yellow-500/50 text-yellow-300",
  info: "bg-cyan-500/20 border-cyan-500/50 text-cyan-300",
};

export function IssueCard({ issue }: IssueCardProps) {
  return (
    <div className="bg-slate-800 border border-white/10 rounded-2xl p-4">
      <div className="flex justify-between gap-2">
        <strong>{issue.code}</strong>
        <Badge className={SEVERITY_COLORS[issue.severity] || ""}>{issue.severity}</Badge>
      </div>
      <div className="text-xs opacity-90 mt-1.5">{issue.message}</div>
      {issue.evidence && (
        <div className="mt-2.5">
          <CodeBlock>{issue.evidence}</CodeBlock>
        </div>
      )}
    </div>
  );
}
