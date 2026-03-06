export type Issue = {
  code: string;
  severity: "info" | "warning" | "critical";
  message: string;
  evidence?: string | null;
};

export type Suggestion = {
  title: string;
  impact: "low" | "medium" | "high";
  rationale: string;
  actions: string[];
  index_sql: string[];
  rewrite_sql?: string | null;
  caveats: string[];
};

export type AnalyzeResponse = {
  dialect: string;
  normalized_sql: string;
  parsed: boolean;
  structure: any;
  execution_sequence: Array<{
    step: number;
    clause: string;
    description: string;
    sql?: string;
  }>;
  explanation: string;
  breakdown: string[];
  assumptions: string[];
  issues: Issue[];
  suggestions: Suggestion[];
  rewritten_sql?: string | null;
  confidence: "low" | "medium" | "high";
};
