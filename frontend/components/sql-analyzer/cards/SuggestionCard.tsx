import { Suggestion } from "../types";
import { Badge } from "../../ui/Badge";
import { CodeBlock } from "../../ui/CodeBlock";
import { SqlViewerSection } from "../SqlViewerSection";

interface SuggestionCardProps {
  suggestion: Suggestion;
  onCopy: (text: string) => void;
  copied?: boolean;
}

const IMPACT_COLORS: Record<string, string> = {
  high: "bg-purple-500/20 border-purple-500/50 text-purple-300",
  medium: "bg-blue-500/20 border-blue-500/50 text-blue-300",
  low: "bg-green-500/20 border-green-500/50 text-green-300",
};

export function SuggestionCard({ suggestion, onCopy, copied }: SuggestionCardProps) {
  return (
    <div className="bg-slate-800 border border-white/10 rounded-2xl p-4">
      <div className="flex justify-between gap-2">
        <strong>{suggestion.title}</strong>
        <Badge className={IMPACT_COLORS[suggestion.impact] || ""}>{suggestion.impact}</Badge>
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
        <SqlViewerSection
          value={suggestion.index_sql.join("\n")}
          onCopy={onCopy}
          copied={copied}
          sectionLabel="Index SQL"
        />
      )}

      {suggestion.rewrite_sql && (
        <SqlViewerSection
          value={suggestion.rewrite_sql}
          onCopy={onCopy}
          copied={copied}
          sectionLabel="Suggested rewrite"
        />
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
