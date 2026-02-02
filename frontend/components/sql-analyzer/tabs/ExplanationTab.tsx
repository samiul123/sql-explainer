import { AnalyzeResponse } from "../types";
import { CodeBlock } from "../../ui/CodeBlock";
import { SectionLabel } from "../../ui/SectionLabel";

interface ExplanationTabProps {
  result: AnalyzeResponse;
}

export function ExplanationTab({ result }: ExplanationTabProps) {
  return (
    <div className="grid gap-3">
      <div>
        <SectionLabel>Summary</SectionLabel>
        <CodeBlock>{result.explanation}</CodeBlock>
      </div>

      <div>
        <SectionLabel>Breakdown</SectionLabel>
        <CodeBlock>
          {result.breakdown.map((b, i) => `${i + 1}. ${b}`).join("\n")}
        </CodeBlock>
      </div>

      <div>
        <SectionLabel>Assumptions</SectionLabel>
        <CodeBlock>
          {(result.assumptions?.length ? result.assumptions : ["(none)"]).join("\n")}
        </CodeBlock>
      </div>

      <div>
        <SectionLabel>Parsed structure (debug)</SectionLabel>
        <CodeBlock>{JSON.stringify(result.structure, null, 2)}</CodeBlock>
      </div>
    </div>
  );
}
