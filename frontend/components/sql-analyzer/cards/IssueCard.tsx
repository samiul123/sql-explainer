import { Issue } from "../types";
import { Badge } from "../../ui/Badge";
import { CodeBlock } from "../../ui/CodeBlock";

interface IssueCardProps {
  issue: Issue;
}

export function IssueCard({ issue }: IssueCardProps) {
  return (
    <div className="bg-slate-800 border border-white/10 rounded-2xl p-4">
      <div className="flex justify-between gap-2">
        <strong>{issue.code}</strong>
        <Badge>{issue.severity}</Badge>
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
