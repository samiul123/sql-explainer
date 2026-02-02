import { createTheme } from "@uiw/codemirror-themes";
import { tags as t } from "@lezer/highlight";

export const sqlExplainerTheme = createTheme({
  theme: "dark",
  settings: {
    background: "#0f172a", // slate-950
    foreground: "#e2e8f0", // slate-200
    caret: "#60a5fa", // blue-400
    selection: "#1e40af40", // blue-700 with transparency
    selectionMatch: "#1e40af30",
    lineHighlight: "#1e293b", // slate-800
    gutterBackground: "#0f172a", // slate-950
    gutterForeground: "#64748b", // slate-500
    gutterBorder: "#1e293b",
  },
  styles: [
    { tag: t.comment, color: "#64748b" }, // slate-500
    { tag: t.keyword, color: "#c084fc" }, // purple-400
    { tag: [t.string, t.special(t.string)], color: "#86efac" }, // green-300
    { tag: t.number, color: "#fbbf24" }, // amber-400
    { tag: t.bool, color: "#fbbf24" },
    { tag: t.null, color: "#f87171" }, // red-400
    { tag: t.operator, color: "#60a5fa" }, // blue-400
    { tag: t.function(t.variableName), color: "#38bdf8" }, // sky-400
    { tag: t.typeName, color: "#2dd4bf" }, // teal-400
    { tag: t.definition(t.variableName), color: "#e2e8f0" },
    { tag: t.variableName, color: "#e2e8f0" },
    { tag: t.propertyName, color: "#fbbf24" },
  ],
});
