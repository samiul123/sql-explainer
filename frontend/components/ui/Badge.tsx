interface BadgeProps {
  children: React.ReactNode;
  className?: string;
}

export function Badge({ children, className = "" }: BadgeProps) {
  return (
    <span className={`text-xs px-2 py-1 rounded-full border border-white/10 whitespace-nowrap ${className}`}>
      {children}
    </span>
  );
}
