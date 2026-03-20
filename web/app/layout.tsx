import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nexus — Autonomous Agent",
  description: "Self-funding autonomous agent powered by wstETH yield",
};

const NAV_LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/agents", label: "Agents" },
  { href: "/economy", label: "Economy" },
  { href: "/live", label: "Live Feed" },
];

function TopNav() {
  return (
    <nav style={{
      position: "sticky",
      top: 0,
      zIndex: 50,
      background: "#0f0f1a",
      borderBottom: "1px solid #313244",
      display: "flex",
      alignItems: "center",
      padding: "0 32px",
      height: 52,
      gap: 32,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginRight: 16 }}>
        <div style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          background: "linear-gradient(135deg,#4f46e5,#818cf8)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 13,
          fontWeight: 800,
          color: "white",
          flexShrink: 0,
          boxShadow: "0 0 10px rgba(99,102,241,0.35)",
        }}>N</div>
        <span style={{ fontWeight: 700, fontSize: 14, color: "#818cf8", letterSpacing: "0.02em" }}>Nexus</span>
      </div>
      {NAV_LINKS.map(link => (
        <Link
          key={link.href}
          href={link.href}
          style={{
            fontSize: 13,
            fontWeight: 500,
            color: "#9ca3af",
            textDecoration: "none",
            padding: "6px 0",
            borderBottom: "2px solid transparent",
            transition: "color 0.15s",
          }}
          onMouseOver={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = "#e2e8f0" }}
          onMouseOut={(e) => { (e.currentTarget as HTMLAnchorElement).style.color = "#9ca3af" }}
        >
          {link.label}
        </Link>
      ))}
      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "#34d399" }}>
        <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#34d399", display: "inline-block", animation: "pulse 2s infinite" }} />
        Autonomous
      </div>
    </nav>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "'Inter', system-ui, sans-serif", background: "#0a0a0f", color: "#e2e8f0" }}>
        <TopNav />
        {children}
      </body>
    </html>
  );
}
