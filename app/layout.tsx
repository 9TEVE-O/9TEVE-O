import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Rustic Ledger",
  description: "A tactile family recipe-book prototype with active cook mode.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
