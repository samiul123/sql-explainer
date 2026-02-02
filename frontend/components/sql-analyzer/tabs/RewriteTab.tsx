import { AnalyzeResponse } from "../types";
import { CodeBlock } from "../../ui/CodeBlock";
import { SectionLabel } from "../../ui/SectionLabel";

interface RewriteTabProps {
  result: AnalyzeResponse;
  onCopy: (text: string) => void;
}

export function RewriteTab({ result, onCopy }: RewriteTabProps) {
  return (
    <div className="grid gap-3">
      <div>
        <SectionLabel>Rewritten SQL (top-level)</SectionLabel>
        <CodeBlock>{result.rewritten_sql || "(no rewritten SQL returned)"}</CodeBlock>
        {result.rewritten_sql && (
          <button
            onClick={() => onCopy(result.rewritten_sql!)}
            className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm"
          >
            Copy rewritten SQL
          </button>
        )}
      </div>

      <div>
        <SectionLabel>Normalized SQL (what the backend analyzed)</SectionLabel>
        <CodeBlock>{result.normalized_sql}</CodeBlock>
        <button
          onClick={() => onCopy(result.normalized_sql)}
          className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm"
        >
          Copy normalized SQL
        </button>
      </div>
    </div>
  );
}
