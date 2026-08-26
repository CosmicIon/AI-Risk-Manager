import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Risk Manager — BFSI Fraud & Loss Prevention",
  description: "Production-grade AI Risk Management dashboard for real-time fraud scoring, chargeback evidence automation, and return-abuse mitigation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
