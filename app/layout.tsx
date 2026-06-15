import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Evidence-first AI Portfolio",
  description: "A recruiter-friendly portfolio grounded in structured project evidence.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
