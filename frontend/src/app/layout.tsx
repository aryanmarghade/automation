import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "NexusFlow AI — Independent AI Agent & Visual Automation Platform",
  description: "Native Windows 11 Local-First AI Agent & Node-based Workflow Engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-900 text-slate-100 flex h-screen overflow-hidden antialiased`}>
        <Sidebar />
        <main className="flex-1 flex flex-col h-screen overflow-y-auto bg-slate-900/50">
          {children}
        </main>
      </body>
    </html>
  );
}
