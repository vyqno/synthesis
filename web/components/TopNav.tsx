"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import WalletButton from "./WalletButton";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/agents", label: "Operators" },
  { href: "/economy", label: "Market" },
  { href: "/live", label: "Activity" },
];

export default function TopNav() {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  return (
    <nav style={{
      position: "fixed",
      top: 0, left: 0, right: 0,
      zIndex: 1000,
      height: 60,
      display: "flex",
      alignItems: "center",
      padding: "0 32px",
      background: isLanding ? "transparent" : "rgba(2,6,23,0.88)",
      backdropFilter: isLanding ? "none" : "blur(20px)",
      WebkitBackdropFilter: isLanding ? "none" : "blur(20px)",
      borderBottom: isLanding ? "none" : "1px solid rgba(255,255,255,0.05)",
      transition: "background 0.3s, border-color 0.3s",
    }}>

      {/* Logo */}
      <Link href="/" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", marginRight: 36 }}>
        <div style={{
          width: 30, height: 30,
          background: "linear-gradient(135deg,#2dd4bf,#818cf8)",
          borderRadius: 8,
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0,
        }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 2L14 5.5V10.5L8 14L2 10.5V5.5L8 2Z" stroke="white" strokeWidth="1.5" fill="rgba(255,255,255,0.15)" />
            <circle cx="8" cy="8" r="2.5" fill="white" />
          </svg>
        </div>
        <span style={{ fontWeight: 700, fontSize: 16, color: "#fff", letterSpacing: "-0.02em" }}>
          nexus<span style={{ color: "#2dd4bf" }}>.</span>
        </span>
      </Link>

      {/* Nav links */}
      {!isLanding && (
        <div style={{ display: "flex", alignItems: "center", gap: 2, flex: 1 }}>
          {NAV_LINKS.map(link => {
            const active = pathname === link.href || pathname.startsWith(link.href + "/");
            return (
              <Link
                key={link.href}
                href={link.href}
                style={{
                  fontSize: 13,
                  fontWeight: active ? 600 : 400,
                  color: active ? "#f1f5f9" : "#64748b",
                  textDecoration: "none",
                  padding: "5px 13px",
                  borderRadius: 7,
                  background: active ? "rgba(255,255,255,0.06)" : "transparent",
                  transition: "all 0.15s",
                }}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      )}

      {isLanding && <div style={{ flex: 1 }} />}

      {/* Right */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {!isLanding && (
          <div style={{
            display: "flex", alignItems: "center", gap: 5,
            fontSize: 11, color: "#34d399", fontWeight: 500,
            padding: "4px 10px", borderRadius: 20,
            background: "rgba(52,211,153,0.06)",
            border: "1px solid rgba(52,211,153,0.12)",
          }}>
            <span className="pulse" style={{ width: 5, height: 5, borderRadius: "50%", background: "#34d399", display: "inline-block" }} />
            Mainnet
          </div>
        )}
        <WalletButton />
      </div>
    </nav>
  );
}
