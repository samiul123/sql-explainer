import { SqlEditor } from "./SqlEditor";

interface InputPanelProps {
  dialect: string;
  sql: string;
  schemaText: string;
  loading: boolean;
  error: string | null;
  onDialectChange: (dialect: string) => void;
  onSqlChange: (sql: string) => void;
  onSchemaChange: (schema: string) => void;
  onAnalyze: () => void;
}

export function InputPanel({
  dialect,
  sql,
  schemaText,
  loading,
  error,
  onDialectChange,
  onSqlChange,
  onSchemaChange,
  onAnalyze,
}: InputPanelProps) {
  return (
    <div className="bg-slate-900 border border-white/10 rounded-2xl p-4 grid gap-3">
      <div>
        <label className="block text-xs opacity-90 mb-1.5">Dialect</label>
        <select
          value={dialect}
          onChange={(e) => onDialectChange(e.target.value)}
          className="w-full bg-slate-950 text-slate-100 border border-white/10 rounded-lg px-2.5 py-2.5 outline-none"
        >
          <option value="postgres">Postgres</option>
          <option value="mysql">MySQL</option>
          <option value="sqlite">SQLite</option>
          <option value="tsql">SQL Server (T-SQL)</option>
          <option value="bigquery">BigQuery</option>
          <option value="snowflake">Snowflake</option>
        </select>
      </div>

      <div>
        <label className="block text-xs opacity-90 mb-1.5">SQL</label>
        <SqlEditor
          value={sql}
          onChange={onSqlChange}
          placeholder="Enter your SQL query..."
        />
      </div>

      <div>
        <label className="block text-xs opacity-90 mb-1.5">Schema (optional)</label>
        <SqlEditor
          value={schemaText}
          onChange={onSchemaChange}
          placeholder="CREATE TABLE users (id INT PRIMARY KEY, ...);"
        />
      </div>

      <button
        onClick={onAnalyze}
        disabled={loading || !sql.trim()}
        className="bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white px-3 py-2.5 rounded-lg font-semibold"
      >
        {loading ? "Analyzing..." : "Analyze"}
      </button>

      {error && <div className="text-xs opacity-90 text-red-400">{error}</div>}
    </div>
  );
}
