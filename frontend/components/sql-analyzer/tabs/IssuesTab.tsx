import { Issue } from "../types";
import { IssueCard } from "../cards/IssueCard";
import { CodeBlock } from "../../ui/CodeBlock";

interface IssuesTabProps {
  issues: Issue[];
}

export function IssuesTab({ issues }: IssuesTabProps) {
  if (issues.length === 0) {
    return (
      <CodeBlock>No issues detected by static rules.</CodeBlock>
    );
  }

  return (
    <div className="grid gap-3">
      {issues.map((issue, idx) => (
        <IssueCard key={idx} issue={issue} />
      ))}
    </div>
  );
}
