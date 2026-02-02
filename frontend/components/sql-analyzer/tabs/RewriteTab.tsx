import { AnalyzeResponse } from "../types";
import { SqlEditor } from "../SqlEditor";
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
        {result.rewritten_sql ? (
          <>
            <SqlEditor
              value={result.rewritten_sql}
              readOnly
            />
            <button
              onClick={() => onCopy(result.rewritten_sql!)}
              className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm"
            >
              Copy rewritten SQL
            </button>
          </>
        ) : (
          <CodeBlock>(no rewritten SQL returned)</CodeBlock>
        )}
      </div>

      <div>
        <SectionLabel>Normalized SQL (what the backend analyzed)</SectionLabel>
        <SqlEditor
          value={result.normalized_sql}
          readOnly
        />
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
