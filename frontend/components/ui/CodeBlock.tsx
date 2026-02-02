interface CodeBlockProps {
  children: string;
  className?: string;
}

export function CodeBlock({ children, className = "" }: CodeBlockProps) {
  return (
    <pre className={`whitespace-pre-wrap break-words bg-slate-950 px-3 py-3 rounded-xl border border-white/10 text-sm leading-relaxed m-0 ${className}`}>
      {children}
    </pre>
  );
}
