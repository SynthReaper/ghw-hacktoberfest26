import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CouchPotato Expenses — Sloth Command Center",
  description: "Zero-Click Invoice & Receipt Hunter for Hacktoberfest Week 3 (Slow and Steady)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-obsidian-950 text-zinc-100 selection:bg-amber-500/20 selection:text-amber-300">
        {children}
      </body>
    </html>
  );
}
