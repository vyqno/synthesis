"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useWallet, CHAIN_NAMES } from "@/hooks/useWallet";

export default function WalletButton() {
  const { address, chainId, balance, isConnected, isConnecting, error, connect, disconnect } = useWallet();
  const [open, setOpen] = useState(false);

  const short = address ? `${address.slice(0, 6)}…${address.slice(-4)}` : "";
  const chainName = chainId ? (CHAIN_NAMES[chainId] ?? `Chain ${chainId}`) : "";

  if (isConnected && address) {
    return (
      <div style={{ position: "relative" }}>
        <button
          onClick={() => setOpen(o => !o)}
          style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "6px 12px 6px 8px",
            borderRadius: 10,
            background: "rgba(45,212,191,0.07)",
            border: "1px solid rgba(45,212,191,0.2)",
            color: "#f1f5f9", fontSize: 12, fontWeight: 600,
            cursor: "pointer", fontFamily: "inherit",
          }}
        >
          <span className="pulse" style={{ width: 8, height: 8, borderRadius: "50%", background: "#34d399", display: "inline-block", flexShrink: 0 }} />
          <span style={{ fontFamily: "monospace", color: "#2dd4bf" }}>{short}</span>
          {balance && (
            <span style={{ color: "#475569", borderLeft: "1px solid rgba(255,255,255,0.08)", paddingLeft: 8 }}>
              {balance}
            </span>
          )}
        </button>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ opacity: 0, y: 6, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 4, scale: 0.97 }}
              transition={{ duration: 0.14 }}
              style={{
                position: "absolute", right: 0, top: "calc(100% + 8px)",
                background: "#0b1120",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 12, padding: 8,
                minWidth: 240, zIndex: 200,
                boxShadow: "0 20px 48px rgba(0,0,0,0.6)",
              }}
            >
              <div style={{ padding: "10px 12px 12px", borderBottom: "1px solid rgba(255,255,255,0.05)", marginBottom: 6 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span style={{ fontSize: 11, color: "#475569" }}>Connected</span>
                  <span style={{ fontSize: 11, color: "#34d399", fontWeight: 600 }}>{chainName}</span>
                </div>
                <div style={{ fontSize: 11, fontFamily: "monospace", color: "#64748b", wordBreak: "break-all" }}>{address}</div>
              </div>
              <button
                onClick={() => { disconnect(); setOpen(false); }}
                style={{
                  width: "100%", padding: "8px 12px", borderRadius: 7,
                  border: "none", background: "rgba(251,113,133,0.06)",
                  color: "#fb7185", fontSize: 12, fontWeight: 600,
                  cursor: "pointer", textAlign: "left", fontFamily: "inherit",
                }}
              >
                Disconnect
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  return (
    <div>
      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={connect}
        disabled={isConnecting}
        title={error ?? undefined}
        style={{
          padding: "7px 18px",
          borderRadius: 10,
          background: "linear-gradient(135deg,#2dd4bf,#0ea5e9)",
          border: "none",
          color: "#020617",
          fontSize: 13,
          fontWeight: 700,
          cursor: isConnecting ? "wait" : "pointer",
          opacity: isConnecting ? 0.7 : 1,
          fontFamily: "inherit",
          letterSpacing: "-0.01em",
        }}
      >
        {isConnecting ? "Connecting…" : "Connect Wallet"}
      </motion.button>
      {error && (
        <div style={{ position: "absolute", top: "calc(100% + 6px)", right: 0, fontSize: 11, color: "#fb7185", background: "#0b1120", border: "1px solid rgba(251,113,133,0.2)", padding: "6px 10px", borderRadius: 7, whiteSpace: "nowrap", maxWidth: 260 }}>
          {error}
        </div>
      )}
    </div>
  );
}
