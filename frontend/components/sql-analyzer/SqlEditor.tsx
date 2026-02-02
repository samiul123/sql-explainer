"use client";

import { useCallback } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { sql } from "@codemirror/lang-sql";
import { EditorView } from "@codemirror/view";
import { sqlExplainerTheme } from "./editorTheme";

interface SqlEditorProps {
  value: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  minHeight?: string;
  readOnly?: boolean;
}

export function SqlEditor({
  value,
  onChange = () => {},
  placeholder = "Enter SQL query...",
  minHeight = "176px",
  readOnly = false,
}: SqlEditorProps) {
  const handleChange = useCallback(
    (val: string) => {
      if (!readOnly) {
        onChange(val);
      }
    },
    [onChange, readOnly]
  );

  return (
    <div className="border border-white/10 rounded-lg overflow-hidden">
      <CodeMirror
        value={value}
        height={minHeight}
        theme={sqlExplainerTheme}
        extensions={[sql(), EditorView.lineWrapping]}
        onChange={handleChange}
        placeholder={placeholder}
        basicSetup={{
          lineNumbers: true,
          highlightActiveLineGutter: true,
          highlightSpecialChars: true,
          foldGutter: true,
          drawSelection: !readOnly,
          dropCursor: !readOnly,
          allowMultipleSelections: !readOnly,
          indentOnInput: !readOnly,
          bracketMatching: true,
          closeBrackets: !readOnly,
          autocompletion: !readOnly,
          rectangularSelection: !readOnly,
          crosshairCursor: true,
          highlightActiveLine: true,
          highlightSelectionMatches: true,
          closeBracketsKeymap: !readOnly,
          searchKeymap: true,
          foldKeymap: true,
          completionKeymap: !readOnly,
          lintKeymap: true,
        }}
        editable={!readOnly}
        style={{
          fontSize: "14px",
          fontFamily:
            "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        }}
        className="sql-editor"
      />
    </div>
  );
}
