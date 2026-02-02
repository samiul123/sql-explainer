interface SectionLabelProps {
  children: React.ReactNode;
}

export function SectionLabel({ children }: SectionLabelProps) {
  return (
    <div className="text-xs opacity-90 mb-1.5">
      {children}
    </div>
  );
}
