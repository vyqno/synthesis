"use client";
import { useState } from "react";

const TREASURY = {
  principal_wsteth: 1.0,
  yield_eth: 0.0042,
  yield_usd: 10.08,
  apy: 4.2,
};

const MCP_SERVERS = [
  { name: "nexus-lido-mcp", tools: 8, status: "online" },
  { name: "nexus-treasury-mcp", tools: 8, status: "online" },
  { name: "nexus-identity-mcp", tools: 10, status: "online" },
  { name: "nexus-trade-mcp", tools: 8, status: "online" },
  { name: "nexus-storage-mcp", tools: 6, status: "online" },
  { name: "nexus-coordinate-mcp", tools: 7, status: "online" },
  { name: "nexus-goods-mcp", tools: 6, status: "online" },
  { name: "nexus-secrets-mcp", tools: 4, status: "online" },
];

const TOP_TRACKS = [
  { name: "Synthesis Open", prize: 28308 },
  { name: "Venice Private Agents", prize: 11500 },
  { name: "EigenCompute", prize: 5000 },
  { name: "Base Trading", prize: 5000 },
  { name: "Bankr Gateway", prize: 5000 },
  { name: "Lido MCP", prize: 5000 },
  { name: "Uniswap API", prize: 5000 },
  { name: "MetaMask Delegations", prize: 5000 },
  { name: "Celo Best Agent", prize: 5000 },
  { name: "Base Agent Services", prize: 5000 },
];

const SUB_AGENTS = [
  { name: "nexus-trader", status: "Active", budget: "0.002 ETH", lastAction: "Placed limit order on Uniswap" },
  { name: "nexus-staker", status: "Active", budget: "0.5 ETH", lastAction: "Staked via Lido wstETH vault" },
  { name: "nexus-scorer", status: "Idle", budget: "0.001 ETH", lastAction: "Scored 3 public goods projects" },
  { name: "nexus-keeper", status: "Active", budget: "0.001 ETH", lastAction: "Checked vault yield threshold" },
  { name: "nexus-prover", status: "Idle", budget: "0.001 ETH", lastAction: "Generated ZK identity proof" },
  { name: "nexus-monitor", status: "Active", budget: "0.000 ETH", lastAction: "Monitoring 46 track deadlines" },
];

const AGENT_LOG = [
  { ts: "2026-03-20T09:14:32Z", action: "stake", result: "Staked 0.1 ETH → received 0.0942 wstETH" },
  { ts: "2026-03-20T09:10:11Z", action: "get_vault_yield", result: "Yield: 0.0042 ETH ($10.08) available" },
  { ts: "2026-03-20T09:05:44Z", action: "score_public_good", result: "EigenCompute scored 87/100" },
  { ts: "2026-03-20T08:58:19Z", action: "generate_proof", result: "ZK proof generated for identity claim" },
  { ts: "2026-03-20T08:45:00Z", action: "register_identity", result: "nexus-agent.eth registered on Base" },
];

const NAV_ITEMS = ["Dashboard", "Treasury", "MCP Servers", "Tracks", "Agent Log"];

function formatTs(ts: string) {
  const d = new Date(ts);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
}

export default function Home() {
  const [activeNav, setActiveNav] = useState("Dashboard");
  const [actionLog, setActionLog] = useState<string[]>([]);

  const runAction = (label: string, detail: string) => {
    setActionLog((prev) => [`[${new Date().toLocaleTimeString()}] ${label} — ${detail}`, ...prev.slice(0, 9)]);
  };

  const maxPrize = TOP_TRACKS[0].prize;

  return (
    <div style={{ display: "flex", height: "100vh", background: "var(--bg)", overflow: "hidden" }}>
      {/* Sidebar */}
      <aside style={{
        width: 240,
        background: "var(--surface)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        padding: "20px 16px",
        gap: 24,
        flexShrink: 0,
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 38,
            height: 38,
            borderRadius: "50%",
            background: "linear-gradient(135deg,#4f46e5,#818cf8)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
            fontWeight: 800,
            color: "white",
            flexShrink: 0,
            boxShadow: "0 0 16px rgba(99,102,241,0.4)",
          }}>
            N
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: "#818cf8" }}>Nexus</div>
            <div style={{ fontSize: 11, color: "var(--muted)" }}>nexus-agent.eth</div>
          </div>
        </div>

        {/* Status */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "8px 12px",
          background: "rgba(16,185,129,0.08)",
          border: "1px solid rgba(16,185,129,0.2)",
          borderRadius: 8,
        }}>
          <div className="pulse" style={{ width: 7, height: 7, borderRadius: "50%", background: "#10b981", flexShrink: 0 }} />
          <span style={{ fontSize: 12, fontWeight: 600, color: "#10b981" }}>Autonomous</span>
        </div>

        {/* Nav */}
        <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {NAV_ITEMS.map((item) => (
            <button
              key={item}
              onClick={() => setActiveNav(item)}
              style={{
                textAlign: "left",
                padding: "9px 12px",
                borderRadius: 8,
                border: "none",
                background: activeNav === item ? "rgba(99,102,241,0.15)" : "transparent",
                color: activeNav === item ? "#818cf8" : "var(--muted)",
                fontSize: 13,
                fontWeight: activeNav === item ? 600 : 400,
                cursor: "pointer",
                borderLeft: activeNav === item ? "2px solid #6366f1" : "2px solid transparent",
                transition: "all 0.15s",
              }}
              onMouseEnter={(e) => {
                if (activeNav !== item) {
                  e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                  e.currentTarget.style.color = "#e2e8f0";
                }
              }}
              onMouseLeave={(e) => {
                if (activeNav !== item) {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "var(--muted)";
                }
              }}
            >
              {item}
            </button>
          ))}
        </nav>

        {/* Bottom stats */}
        <div style={{ marginTop: "auto", borderTop: "1px solid var(--border)", paddingTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
          <div style={{ fontSize: 11, color: "var(--muted)", display: "flex", justifyContent: "space-between" }}>
            <span>MCP Servers</span>
            <span style={{ color: "#10b981", fontWeight: 600 }}>8 / 8 online</span>
          </div>
          <div style={{ fontSize: 11, color: "var(--muted)", display: "flex", justifyContent: "space-between" }}>
            <span>Total Tools</span>
            <span style={{ color: "#e2e8f0" }}>57 available</span>
          </div>
          <div style={{ fontSize: 11, color: "var(--muted)", display: "flex", justifyContent: "space-between" }}>
            <span>Active Tracks</span>
            <span style={{ color: "#e2e8f0" }}>46 tracks</span>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
        {/* Header */}
        <div style={{ marginBottom: 24, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: "#e2e8f0" }}>
              {activeNav}
            </h1>
            <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--muted)" }}>
              Nexus autonomous agent dashboard · Synthesis 2026
            </p>
          </div>
          <div style={{
            fontSize: 12,
            color: "var(--muted)",
            padding: "6px 12px",
            border: "1px solid var(--border)",
            borderRadius: 6,
            background: "var(--surface)",
          }}>
            {new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
          </div>
        </div>

        {/* Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>

          {/* Card 1: Treasury */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 20,
            gridColumn: "1",
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <h2 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>wstETH Treasury</h2>
              <span style={{
                fontSize: 11,
                padding: "3px 8px",
                borderRadius: 4,
                background: "rgba(16,185,129,0.1)",
                color: "#10b981",
                border: "1px solid rgba(16,185,129,0.2)",
              }}>EarnETH</span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
              <div style={{ background: "var(--surface-2)", borderRadius: 8, padding: "12px 14px" }}>
                <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>Principal</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: "#e2e8f0" }}>{TREASURY.principal_wsteth.toFixed(1)}</div>
                <div style={{ fontSize: 11, color: "var(--muted)" }}>wstETH</div>
              </div>
              <div style={{ background: "var(--surface-2)", borderRadius: 8, padding: "12px 14px" }}>
                <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>Yield Available</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: "#10b981" }}>{TREASURY.yield_eth.toFixed(4)}</div>
                <div style={{ fontSize: 11, color: "var(--muted)" }}>ETH (${TREASURY.yield_usd.toFixed(2)})</div>
              </div>
            </div>

            <div style={{ marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: "var(--muted)" }}>APY</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: "#818cf8" }}>{TREASURY.apy}%</span>
              </div>
              <div style={{ height: 6, background: "var(--surface-2)", borderRadius: 3, overflow: "hidden" }}>
                <div style={{
                  height: "100%",
                  width: `${(TREASURY.yield_eth / TREASURY.principal_wsteth) * 100 * 50}%`,
                  background: "linear-gradient(90deg,#6366f1,#818cf8)",
                  borderRadius: 3,
                  minWidth: "4%",
                }} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
                <span style={{ fontSize: 10, color: "var(--muted)" }}>Yield</span>
                <span style={{ fontSize: 10, color: "var(--muted)" }}>Principal</span>
              </div>
            </div>

            <button
              onClick={() => runAction("Withdraw Yield", `dry_run: would withdraw ${TREASURY.yield_eth} ETH`)}
              style={{
                width: "100%",
                padding: "10px",
                borderRadius: 8,
                border: "1px solid rgba(99,102,241,0.4)",
                background: "rgba(99,102,241,0.1)",
                color: "#818cf8",
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(99,102,241,0.2)";
                e.currentTarget.style.borderColor = "#6366f1";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(99,102,241,0.1)";
                e.currentTarget.style.borderColor = "rgba(99,102,241,0.4)";
              }}
            >
              Withdraw Yield (dry_run)
            </button>
          </div>

          {/* Card 2: MCP Servers */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 20,
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <h2 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>MCP Servers</h2>
              <span style={{ fontSize: 11, color: "var(--muted)" }}>8 / 8 online</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {MCP_SERVERS.map((s) => (
                <div key={s.name} style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 10px",
                  background: "var(--surface-2)",
                  borderRadius: 7,
                  border: "1px solid var(--border)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: s.status === "online" ? "#10b981" : "#64748b",
                      flexShrink: 0,
                    }} />
                    <span style={{ fontSize: 12, color: "#e2e8f0", fontFamily: "monospace" }}>{s.name}</span>
                  </div>
                  <span style={{
                    fontSize: 10,
                    color: "var(--muted)",
                    padding: "2px 6px",
                    background: "rgba(255,255,255,0.04)",
                    borderRadius: 4,
                  }}>
                    {s.tools} tools
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Card 3: Track Coverage */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 20,
          }}>
            <div style={{ marginBottom: 16 }}>
              <h2 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>Track Coverage</h2>
              <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--muted)" }}>46 tracks · $134,458 total prizes</p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
              {TOP_TRACKS.map((t) => (
                <div key={t.name}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                    <span style={{ fontSize: 11, color: "#e2e8f0" }}>{t.name}</span>
                    <span style={{ fontSize: 11, color: "var(--muted)" }}>${t.prize.toLocaleString()}</span>
                  </div>
                  <div style={{ height: 5, background: "var(--surface-2)", borderRadius: 3, overflow: "hidden" }}>
                    <div style={{
                      height: "100%",
                      width: `${(t.prize / maxPrize) * 100}%`,
                      background: t.prize === maxPrize
                        ? "linear-gradient(90deg,#6366f1,#818cf8)"
                        : "linear-gradient(90deg,#1e1b4b,#6366f1)",
                      borderRadius: 3,
                    }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card 4: Agent Log */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 20,
            gridColumn: "1 / 3",
          }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <h2 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>Agent Log</h2>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div className="pulse" style={{ width: 6, height: 6, borderRadius: "50%", background: "#10b981" }} />
                <span style={{ fontSize: 11, color: "var(--muted)" }}>Live</span>
                <button style={{
                  fontSize: 11,
                  color: "#818cf8",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: 0,
                }}>View All</button>
              </div>
            </div>

            {/* Live action log from quick actions */}
            {actionLog.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                {actionLog.slice(0, 2).map((entry, i) => (
                  <div key={i} style={{
                    padding: "8px 12px",
                    background: "rgba(99,102,241,0.08)",
                    border: "1px solid rgba(99,102,241,0.2)",
                    borderRadius: 7,
                    marginBottom: 4,
                    fontSize: 12,
                    color: "#818cf8",
                    fontFamily: "monospace",
                  }}>
                    {entry}
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {AGENT_LOG.map((entry, i) => (
                <div key={i} style={{
                  display: "flex",
                  gap: 12,
                  padding: "10px 12px",
                  background: "var(--surface-2)",
                  borderRadius: 8,
                  border: "1px solid var(--border)",
                  alignItems: "flex-start",
                }}>
                  <span style={{
                    fontSize: 11,
                    color: "var(--muted)",
                    fontFamily: "monospace",
                    flexShrink: 0,
                    marginTop: 1,
                  }}>
                    {formatTs(entry.ts)}
                  </span>
                  <span style={{
                    fontSize: 11,
                    padding: "2px 7px",
                    borderRadius: 4,
                    background: "rgba(99,102,241,0.12)",
                    color: "#818cf8",
                    fontFamily: "monospace",
                    flexShrink: 0,
                  }}>
                    {entry.action}
                  </span>
                  <span style={{ fontSize: 12, color: "#e2e8f0", lineHeight: 1.5 }}>{entry.result}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Card 5: Sub-Agents */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 20,
          }}>
            <h2 style={{ margin: "0 0 16px", fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>Sub-Agents</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {SUB_AGENTS.map((agent) => (
                <div key={agent.name} style={{
                  padding: "10px 12px",
                  background: "var(--surface-2)",
                  borderRadius: 8,
                  border: "1px solid var(--border)",
                }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: "#e2e8f0", fontFamily: "monospace" }}>
                      {agent.name}
                    </span>
                    <span style={{
                      fontSize: 10,
                      padding: "1px 6px",
                      borderRadius: 3,
                      background: agent.status === "Active" ? "rgba(16,185,129,0.12)" : "rgba(100,116,139,0.12)",
                      color: agent.status === "Active" ? "#10b981" : "var(--muted)",
                    }}>
                      {agent.status}
                    </span>
                  </div>
                  <div style={{ fontSize: 10, color: "var(--muted)", marginBottom: 3 }}>
                    Budget: <span style={{ color: "#e2e8f0" }}>{agent.budget}</span>
                  </div>
                  <div style={{ fontSize: 10, color: "var(--muted)", lineHeight: 1.4 }}>
                    {agent.lastAction}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Card 6: Quick Actions */}
          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 20,
            gridColumn: "1",
          }}>
            <h2 style={{ margin: "0 0 16px", fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>Quick Actions</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                {
                  label: "Stake 0.1 ETH",
                  detail: "dry_run: lido-mcp/stake → would stake 0.1 ETH for wstETH",
                  color: "#6366f1",
                  bg: "rgba(99,102,241,0.1)",
                  border: "rgba(99,102,241,0.3)",
                },
                {
                  label: "Get Vault Yield",
                  detail: "lido-mcp/get_vault_yield → 0.0042 ETH available",
                  color: "#10b981",
                  bg: "rgba(16,185,129,0.08)",
                  border: "rgba(16,185,129,0.25)",
                },
                {
                  label: "Score a Project",
                  detail: "goods-mcp/score_public_good → scoring EigenCompute...",
                  color: "#f59e0b",
                  bg: "rgba(245,158,11,0.08)",
                  border: "rgba(245,158,11,0.25)",
                },
                {
                  label: "Generate Proof",
                  detail: "secrets-mcp/generate_proof → ZK identity proof generated",
                  color: "#818cf8",
                  bg: "rgba(129,140,248,0.08)",
                  border: "rgba(129,140,248,0.25)",
                },
              ].map((action) => (
                <button
                  key={action.label}
                  onClick={() => runAction(action.label, action.detail)}
                  style={{
                    padding: "11px 14px",
                    borderRadius: 8,
                    border: `1px solid ${action.border}`,
                    background: action.bg,
                    color: action.color,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.filter = "brightness(1.2)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.filter = "brightness(1)";
                  }}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
