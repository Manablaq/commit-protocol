import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "COMMIT — Onchain Justice for Agent Commerce",
  description:
    "Evidence-bound dispute resolution for autonomous commerce, adjudicated by GenLayer and enforced after finality.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
