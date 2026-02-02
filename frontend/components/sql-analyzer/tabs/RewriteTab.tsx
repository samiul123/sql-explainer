import { AnalyzeResponse } from "../types";
import { SqlViewerSection } from "../SqlViewerSection";

interface RewriteTabProps {
  result: AnalyzeResponse;
  onCopy: (text: string) => void;
  copied?: boolean;
}

export function RewriteTab({ result, onCopy, copied }: RewriteTabProps) {
  return (
    <div className="h-full">
      <SqlViewerSection
        sectionLabel="Rewritten SQL (top-level)"
        sectionClassName="text-lg font-semibold text-white"
        value={result.rewritten_sql}
        onCopy={onCopy}
        copied={copied}
        fallbackMessage="No rewritten SQL returned"
      />
    </div>
  );
}
