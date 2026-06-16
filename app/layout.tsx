import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Evidence-first AI Portfolio",
  description: "A recruiter-friendly portfolio grounded in structured project evidence.",
};

/**
 * Root layout component that wraps the entire application with HTML structure.
 */
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
