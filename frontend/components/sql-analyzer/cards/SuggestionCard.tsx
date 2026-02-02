import { Suggestion } from "../types";
import { Badge } from "../../ui/Badge";
import { CodeBlock } from "../../ui/CodeBlock";
import { SectionLabel } from "../../ui/SectionLabel";

interface SuggestionCardProps {
  suggestion: Suggestion;
  onCopy: (text: string) => void;
}

export function SuggestionCard({ suggestion, onCopy }: SuggestionCardProps) {
  return (
    <div className="bg-slate-800 border border-white/10 rounded-2xl p-4">
      <div className="flex justify-between gap-2">
        <strong>{suggestion.title}</strong>
        <Badge>impact: {suggestion.impact}</Badge>
      </div>

      <div className="text-xs opacity-90 mt-1.5">{suggestion.rationale}</div>

      {suggestion.actions?.length > 0 && (
        <>
          <div className="text-xs opacity-90 mt-2.5">Actions</div>
          <CodeBlock>
            {suggestion.actions.map((a) => `- ${a}`).join("\n")}
          </CodeBlock>
        </>
      )}

      {suggestion.index_sql?.length > 0 && (
        <>
          <div className="text-xs opacity-90 mt-2.5">Index SQL</div>
          <CodeBlock>{suggestion.index_sql.join("\n")}</CodeBlock>
          <button
            onClick={() => onCopy(suggestion.index_sql.join("\n"))}
            className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm"
          >
            Copy index SQL
          </button>
        </>
      )}

      {suggestion.rewrite_sql && (
        <>
          <div className="text-xs opacity-90 mt-2.5">Suggested rewrite</div>
          <CodeBlock>{suggestion.rewrite_sql}</CodeBlock>
          <button
            onClick={() => onCopy(suggestion.rewrite_sql!)}
            className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg font-semibold text-sm"
          >
            Copy rewrite
          </button>
        </>
      )}

      {suggestion.caveats?.length > 0 && (
        <>
          <div className="text-xs opacity-90 mt-2.5">Caveats</div>
          <CodeBlock>
            {suggestion.caveats.map((c) => `- ${c}`).join("\n")}
          </CodeBlock>
        </>
      )}
    </div>
  );
}
