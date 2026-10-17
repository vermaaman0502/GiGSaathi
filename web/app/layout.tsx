import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { AppShell } from "@/components/app-shell";

// self-hosted at build time (no runtime request to Google); Indic scripts fall back to the system's Noto fonts
const inter = Inter({ subsets: ["latin"], display: "swap", variable: "--font-sans" });

export const metadata: Metadata = {
  title: "GigSaathi — Earn more. Claim what you may be entitled to. Know your rights.",
  description: "A multilingual, voice-first AI companion for gig and informal workers in India: earnings, welfare schemes, documents, grievances and safety.",
};
export const viewport: Viewport = { themeColor: "#166534", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="font-sans antialiased">
        <Providers><AppShell>{children}</AppShell></Providers>
      </body>
    </html>
  );
}
