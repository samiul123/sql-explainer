interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}

export function TabButton({ active, onClick, children }: TabButtonProps) {
  return (
    <button
      className={`bg-transparent border ${
        active ? "bg-blue-600/25 border-blue-600/60" : "border-white/10"
      } text-slate-100 px-2.5 py-2 rounded-full cursor-pointer text-xs whitespace-nowrap`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}
