import "./globals.css";

export const metadata = {
  title: "SQL Explain + Optimize",
  description: "LangChain + FastAPI SQL explainer and optimizer",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
