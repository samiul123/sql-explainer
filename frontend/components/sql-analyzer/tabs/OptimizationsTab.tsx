import { Suggestion } from "../types";
import { SuggestionCard } from "../cards/SuggestionCard";
import { CodeBlock } from "../../ui/CodeBlock";

interface OptimizationsTabProps {
  suggestions: Suggestion[];
  onCopy: (text: string) => void;
  copied?: boolean;
}

export function OptimizationsTab({ suggestions, onCopy, copied }: OptimizationsTabProps) {
  if (suggestions.length === 0) {
    return (
      <CodeBlock>No suggestions returned.</CodeBlock>
    );
  }

  return (
    <div className="grid gap-3">
      {suggestions.map((suggestion, idx) => (
        <SuggestionCard key={idx} suggestion={suggestion} onCopy={onCopy} copied={copied} />
      ))}
    </div>
  );
}
