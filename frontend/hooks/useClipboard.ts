import { useState, useCallback } from "react";

interface UseClipboardOptions {
  successDuration?: number;
}

export function useClipboard({ successDuration = 2000 }: UseClipboardOptions = {}) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const copy = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setError(null);

        setTimeout(() => {
          setCopied(false);
        }, successDuration);
      } catch (err) {
        setError(err instanceof Error ? err : new Error("Failed to copy"));
        setCopied(false);
      }
    },
    [successDuration]
  );

  return {
    copy,
    copied,
    error,
  };
}
