import { Inter } from "next/font/google";
import Link from "next/link";
import { LayoutDashboard, BrainCircuit, Activity } from "lucide-react";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Gen-DBA | Database Agent",
  description: "AI-Driven Database Administration Agent",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="app-layout">
          <aside className="sidebar">
            <div className="sidebar-logo">
              <BrainCircuit size={24} color="var(--primary-blue)" />
              <span>Gen-DBA</span>
            </div>
            <nav>
              <Link href="/" className="nav-item">
                <LayoutDashboard size={20} />
                Overview
              </Link>
              <Link href="/agent" className="nav-item">
                <BrainCircuit size={20} />
                Agent Analysis
              </Link>
              <Link href="/performance" className="nav-item">
                <Activity size={20} />
                Performance
              </Link>
            </nav>
          </aside>
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
