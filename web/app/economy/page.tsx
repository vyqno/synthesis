"use client";
import { useEffect, useState } from "react";

const MOCK_LISTINGS = [
  { id: "nexus-scorer", label: "Scorer", capabilities: ["impact_eval", "sybil_check"], price_eth: 0.0001, reputation: 82, status: "available", fills: 142 },
  { id: "nexus-prover", label: "Prover", capabilities: ["zk_proof", "tee_attest"], price_eth: 0.0005, reputation: 91, status: "available", fills: 67 },
  { id: "nexus-trader", label: "Trader", capabilities: ["uniswap_swap", "gmx_perp"], price_eth: 0.001, reputation: 74, status: "busy", fills: 388 },
  { id: "nexus-staker", label: "Staker", capabilities: ["lido_stake", "wsteth_wrap"], price_eth: 0.0002, reputation: 88, status: "available", fills: 201 },
];

const MOCK_ESCROWS = [
  { id: "0x1a2b_1773", to: "0x1a2b…3c4d", amount: 0.0005, description: "ZK proof generation", status: "locked", age: "2m ago" },
  { id: "0x5e6f_1772", to: "0x5e6f…7a8b", amount: 0.0001, description: "Impact evaluation", status: "released", age: "1h ago" },
  { id: "0x9c0d_1771", to: "0x9c0d…1e2f", amount: 0.0002, description: "Lido stake routing", status: "released", age: "3h ago" },
];

const MOCK_TXS = [
  { protocol: "x402", description: "Inference request — Venice", amount: 0.00002, status: "success", ts: "09:14" },
  { protocol: "escrow", description: "ZK proof: api_proof", amount: 0.0005, status: "success", ts: "08:58" },
  { protocol: "x402", description: "Sybil check — Olas mech", amount: 0.00005, status: "success", ts: "08:45" },
  { protocol: "swap", description: "ETH → USDC rebalance", amount: 0.01, status: "success", ts: "07:30" },
  { protocol: "stake", description: "stETH wrap → wstETH", amount: 0.5, status: "success", ts: "06:12" },
];

const PROTOCOL_COLORS: Record<string, string> = {
  x402: "#38bdf8",
  escrow: "#818cf8",
  swap: "#f59e0b",
  stake: "#34d399",
};

function ScoreBadge({ score }: { score: number }) {
  const [label, color] =
    score >= 85 ? ["trusted", "#34d399"] :
    score >= 70 ? ["verified", "#2dd4bf"] :
    ["basic", "#64748b"];
  return (
    <span style={{
      fontSize: 11, fontWeight: 600,
      color, background: `${color}15`,
      padding: "2px 8px", borderRadius: 8,
      border: `1px solid ${color}25`,
    }}>
      {label} · {score}
    </span>
  );
}

export default function EconomyPage() {
  const [data, setData] = useState({ listings: MOCK_LISTINGS, escrows: MOCK_ESCROWS, txs: MOCK_TXS });

  useEffect(() => {
    fetch("/api/economy")
      .then(r => r.json())
      .then(d => { if (d.listings?.length) setData(d); })
      .catch(() => {});
  }, []);

  return (
    <div style={{ padding: "92px 28px 60px", maxWidth: 1200, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", color: "var(--text)", marginBottom: 4 }}>
          Market
        </h1>
        <p style={{ fontSize: 13, color: "var(--text-3)" }}>
          Permissionless operator marketplace — hire agents, monitor escrows, review payment flows.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 20 }}>

        {/* Marketplace table */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
          }}>
            <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>Available Operators</span>
              <span style={{ fontSize: 11, color: "var(--text-3)" }}>{data.listings.filter(l => l.status === "available").length} of {data.listings.length} available</span>
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "var(--surface-2)" }}>
                  {["Operator", "Capabilities", "Price / call", "Reputation", "Fills", ""].map(h => (
                    <th key={h} style={{
                      padding: "10px 18px",
                      textAlign: "left",
                      fontSize: 11,
                      fontWeight: 500,
                      color: "var(--text-3)",
                      letterSpacing: "0.04em",
                      textTransform: "uppercase",
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.listings.map((op, i) => (
                  <tr key={op.id} style={{
                    borderTop: "1px solid var(--border)",
                    opacity: op.status === "busy" ? 0.55 : 1,
                    background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)",
                  }}>
                    <td style={{ padding: "14px 18px" }}>
                      <div style={{ fontWeight: 600, fontSize: 13, color: "var(--text)" }}>{op.label}</div>
                      <div style={{ fontSize: 10, color: "var(--text-3)", fontFamily: "monospace", marginTop: 1 }}>{op.id}</div>
                    </td>
                    <td style={{ padding: "14px 18px" }}>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {op.capabilities.map(c => (
                          <span key={c} style={{
                            fontSize: 10, background: "var(--surface-3)",
                            color: "var(--text-3)", padding: "2px 7px",
                            borderRadius: 4, fontFamily: "monospace",
                          }}>{c}</span>
                        ))}
                      </div>
                    </td>
                    <td style={{ padding: "14px 18px" }}>
                      <span style={{ fontSize: 12, color: "var(--accent)", fontFamily: "monospace", fontWeight: 600 }}>
                        {(op.price_eth * 1e6).toFixed(1)} μETH
                      </span>
                    </td>
                    <td style={{ padding: "14px 18px" }}>
                      <ScoreBadge score={op.reputation} />
                    </td>
                    <td style={{ padding: "14px 18px" }}>
                      <span style={{ fontSize: 12, color: "var(--text-2)", fontFamily: "monospace" }}>{op.fills}</span>
                    </td>
                    <td style={{ padding: "14px 18px" }}>
                      <button
                        disabled={op.status !== "available"}
                        style={{
                          fontSize: 11, fontWeight: 600,
                          padding: "5px 14px", borderRadius: 7,
                          border: "1px solid rgba(45,212,191,0.3)",
                          background: op.status === "available" ? "rgba(45,212,191,0.08)" : "var(--surface-3)",
                          color: op.status === "available" ? "var(--accent)" : "var(--text-3)",
                          cursor: op.status === "available" ? "pointer" : "not-allowed",
                        }}
                      >
                        {op.status === "available" ? "Hire" : "Busy"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Transaction history */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
          }}>
            <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)" }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>Transaction History</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column" }}>
              {data.txs.map((tx, i) => (
                <div key={i} style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "12px 22px",
                  borderBottom: i < data.txs.length - 1 ? "1px solid var(--border)" : "none",
                  gap: 14,
                }}>
                  <span style={{
                    fontSize: 10, fontWeight: 600,
                    padding: "2px 8px", borderRadius: 6,
                    background: `${PROTOCOL_COLORS[tx.protocol] ?? "#64748b"}15`,
                    color: PROTOCOL_COLORS[tx.protocol] ?? "#64748b",
                    border: `1px solid ${PROTOCOL_COLORS[tx.protocol] ?? "#64748b"}25`,
                    minWidth: 50, textAlign: "center",
                  }}>{tx.protocol}</span>
                  <span style={{ flex: 1, fontSize: 12, color: "var(--text-2)" }}>{tx.description}</span>
                  <span style={{ fontSize: 12, fontFamily: "monospace", color: "var(--green)", fontWeight: 600 }}>
                    {tx.amount < 0.001 ? `${(tx.amount * 1e6).toFixed(1)} μETH` : `${tx.amount} ETH`}
                  </span>
                  <span style={{ fontSize: 10, fontFamily: "monospace", color: "var(--text-3)", minWidth: 36 }}>{tx.ts}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right sidebar: escrows */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
          }}>
            <div style={{ padding: "18px 22px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>Escrow Queue</span>
              <span style={{ fontSize: 11, color: "var(--yellow)", fontWeight: 600 }}>
                {data.escrows.filter(e => e.status === "locked").length} pending
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {data.escrows.map((e, i) => (
                <div key={i} style={{
                  padding: "14px 20px",
                  borderBottom: "1px solid var(--border)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>{e.description}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 600,
                      padding: "2px 7px", borderRadius: 5,
                      background: e.status === "locked" ? "var(--yellow-dim)" : "var(--green-dim)",
                      color: e.status === "locked" ? "var(--yellow)" : "var(--green)",
                    }}>{e.status}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                    <span style={{ color: "var(--text-3)", fontFamily: "monospace" }}>{e.to}</span>
                    <span style={{ color: "var(--accent)", fontFamily: "monospace", fontWeight: 600 }}>
                      {(e.amount * 1e6).toFixed(1)} μETH
                    </span>
                  </div>
                  <div style={{ fontSize: 10, color: "var(--text-3)" }}>{e.age}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Volume stats */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            padding: 22,
          }}>
            <div style={{ fontSize: 11, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 16 }}>Protocol Stats</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {[
                { k: "Total volume", v: "0.8241 ETH", color: "var(--text)" },
                { k: "Fees collected", v: "0.00082 ETH", color: "var(--accent)" },
                { k: "Total fills", v: "798", color: "var(--text)" },
                { k: "Avg. fill time", v: "1.4s", color: "var(--green)" },
                { k: "Dispute rate", v: "0.0%", color: "var(--text)" },
              ].map(r => (
                <div key={r.k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                  <span style={{ color: "var(--text-3)" }}>{r.k}</span>
                  <span style={{ color: r.color, fontWeight: 600, fontFamily: "monospace" }}>{r.v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
