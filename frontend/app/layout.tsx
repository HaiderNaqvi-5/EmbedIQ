import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EmbedIQ — Embeddable Website-Specific RAG",
  description: "Create AI assistants grounded strictly in your website content.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}