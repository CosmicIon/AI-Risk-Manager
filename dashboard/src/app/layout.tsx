import type { Metadata } from "next";
import "./globals.css";
import "@/components/layout/layout.css";
import "@/components/dashboard/dashboard.css";
import "@/app/chargebacks/chargebacks.css";
import "@/app/simulation/simulation.css";

import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

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
      <body>
        <div className="app-layout">
          <Sidebar />
          <div className="main-content">
            <Header />
            <main className="page-container">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
