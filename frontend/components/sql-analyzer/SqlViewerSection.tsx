import { SqlEditor } from "./SqlEditor";
import { CodeBlock } from "../ui/CodeBlock";
import { Copy, Check } from "lucide-react";

interface SqlViewerSectionProps {
  value: string | null | undefined;
  onCopy: (text: string) => void;
  copied?: boolean;
  sectionLabel?: string;
  sectionClassName?: string;
  fallbackMessage?: string;
  maxHeight?: string;
}

export function SqlViewerSection({
  value,
  onCopy,
  copied = false,
  sectionLabel,
  sectionClassName = "text-xs opacity-90 mt-2.5 text-white",
  fallbackMessage = "no SQL returned"
}: SqlViewerSectionProps) {
  const handleCopy = () => {
    if (value) {
      onCopy(value);
    }
  };

  return (
    <div className="flex flex-col">
      {sectionLabel && <div className={sectionClassName}>{sectionLabel}</div>}
      {value ? (
        <div className="relative">
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 z-10 p-2 hover:bg-white/10 rounded-md transition-colors"
            title={copied ? "Copied!" : "Copy to clipboard"}
          >
            {copied ? (
              <Check className="w-4 h-4 text-green-400" />
            ) : (
              <Copy className="w-4 h-4 text-slate-400" />
            )}
          </button>
          <div className="h-full">
            <SqlEditor
              value={value}
              readOnly
            />
          </div>
        </div>
      ) : (
        <CodeBlock>{fallbackMessage}</CodeBlock>
      )}
    </div>
  );
}
