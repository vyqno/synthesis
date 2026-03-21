"use client";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const AGENT_COLORS: Record<string, string> = {
  "trader":  "#f59e0b",
  "staker":  "#34d399",
  "scorer":  "#60a5fa",
  "keeper":  "#818cf8",
  "prover":  "#fb7185",
  "monitor": "#2dd4bf",
};

const MOCK_AGENTS = [
  {
    id: "nexus-trader",
    label: "Trader",
    description: "DCA & perpetuals execution",
    status: "active",
    budget: { allocated: 0.05, spent: 0.012 },
    last_action: "DCA: 0.01 ETH @ $3,241.50",
    cycles: 47,
    uptime_seconds: 8040,
    network: "Arbitrum",
    protocol: "GMX · Uniswap",
  },
  {
    id: "nexus-staker",
    label: "Staker",
    description: "Lido staking & yield management",
    status: "idle",
    budget: { allocated: 0.02, spent: 0.003 },
    last_action: "Wrapped 0.5 stETH → wstETH",
    cycles: 12,
    uptime_seconds: 8040,
    network: "Mainnet",
    protocol: "Lido",
  },
  {
    id: "nexus-scorer",
    label: "Scorer",
    description: "Impact evaluation & anti-sybil",
    status: "idle",
    budget: { allocated: 0.01, spent: 0.001 },
    last_action: "Scored project: impact=82, sybil=91",
    cycles: 5,
    uptime_seconds: 8040,
    network: "Mainnet",
    protocol: "Olas · Venice",
  },
  {
    id: "nexus-keeper",
    label: "Keeper",
    description: "Treasury & gas price guardian",
    status: "active",
    budget: { allocated: 0.005, spent: 0.0 },
    last_action: "Gas: 18 gwei — threshold OK",
    cycles: 96,
    uptime_seconds: 8040,
    network: "Mainnet",
    protocol: "ERC-4626",
  },
  {
    id: "nexus-prover",
    label: "Prover",
    description: "ZK identity & computation proofs",
    status: "idle",
    budget: { allocated: 0.005, spent: 0.0 },
    last_action: "Proof cached: api_proof",
    cycles: 3,
    uptime_seconds: 8040,
    network: "Base",
    protocol: "Noir · Lit",
  },
  {
    id: "nexus-monitor",
    label: "Monitor",
    description: "Protocol health & alert system",
    status: "active",
    budget: { allocated: 0.002, spent: 0.0 },
    last_action: "Vault APY: 4.21% — no alerts",
    cycles: 32,
    uptime_seconds: 8040,
    network: "All",
    protocol: "Chainlink",
  },
];

function formatUptime(secs: number) {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function AgentCard({ agent }: { agent: typeof MOCK_AGENTS[0] }) {
  const key = (agent.label ?? agent.id?.split("-").pop() ?? "").toLowerCase();
  const color = AGENT_COLORS[key] ?? "#818cf8";
  const pct = agent.budget.allocated > 0 ? (agent.budget.spent / agent.budget.allocated) * 100 : 0;
  const active = agent.status === "active";

  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius-lg)",
      padding: 24,
      display: "flex",
      flexDirection: "column",
      gap: 16,
      transition: "border-color 0.15s",
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 10,
            background: `${color}12`,
            border: `1px solid ${color}25`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}>
            <div style={{ width: 14, height: 14, borderRadius: "50%", background: color, opacity: active ? 1 : 0.3 }} />
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text)" }}>{agent.label}</div>
            <div style={{ fontSize: 11, color: "var(--text-3)", marginTop: 1 }}>{agent.description}</div>
          </div>
        </div>
        <span style={{
          fontSize: 11, fontWeight: 600,
          padding: "3px 9px", borderRadius: 20,
          background: active ? "var(--green-dim)" : "var(--surface-3)",
          color: active ? "var(--green)" : "var(--text-3)",
          border: active ? "1px solid rgba(52,211,153,0.15)" : "1px solid var(--border)",
          display: "flex", alignItems: "center", gap: 5,
        }}>
          {active && <span className="pulse" style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--green)", display: "inline-block" }} />}
          {agent.status}
        </span>
      </div>

      {/* Budget bar */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-3)", marginBottom: 6 }}>
          <span>Budget used</span>
          <span style={{ fontFamily: "monospace" }}>
            {(agent.budget.spent * 1000).toFixed(2)}m / {(agent.budget.allocated * 1000).toFixed(2)}m ETH
          </span>
        </div>
        <div style={{ height: 4, background: "var(--surface-3)", borderRadius: 2, overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: `${pct}%`,
            background: pct > 80 ? "var(--red)" : color,
            borderRadius: 2,
            transition: "width 0.4s ease",
          }} />
        </div>
      </div>

      {/* Last action */}
      <div style={{
        background: "var(--surface-2)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-sm)",
        padding: "10px 12px",
        fontSize: 12,
        color: "var(--text-2)",
        fontFamily: "monospace",
      }}>
        {agent.last_action}
      </div>

      {/* Footer */}
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-3)" }}>
        <div style={{ display: "flex", gap: 14 }}>
          <span>{agent.cycles} cycles</span>
          <span>{formatUptime(agent.uptime_seconds)} uptime</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <span style={{
            padding: "1px 7px", borderRadius: 4,
            background: "var(--surface-3)",
            color: "var(--text-3)", fontSize: 10, fontWeight: 500,
          }}>{agent.network}</span>
          <span style={{
            padding: "1px 7px", borderRadius: 4,
            background: `${color}10`,
            color: color, fontSize: 10, fontWeight: 500,
          }}>{agent.protocol.split("·")[0].trim()}</span>
        </div>
      </div>
    </div>
  );
}

export default function AgentsPage() {
  const [agents, setAgents] = useState(MOCK_AGENTS);

  useEffect(() => {
    fetch("/api/agents")
      .then(r => r.json())
      .then(data => { if (Array.isArray(data) && data.length > 0) setAgents(data); })
      .catch(() => {});
  }, []);

  const activeCount = agents.filter(a => a.status === "active").length;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}
      style={{ padding: "32px 28px 60px", maxWidth: 1200, margin: "0 auto", paddingTop: 92 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", color: "var(--text)", marginBottom: 4 }}>
            Operators
          </h1>
          <p style={{ fontSize: 13, color: "var(--text-3)" }}>
            Autonomous protocol operators — each runs continuously, spending yield to take on-chain actions.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{
            padding: "6px 14px", borderRadius: 8,
            background: "var(--surface)", border: "1px solid var(--border)",
            fontSize: 12, color: "var(--text-2)",
          }}>
            <span style={{ color: "var(--green)", fontWeight: 600 }}>{activeCount}</span>
            <span style={{ color: "var(--text-3)" }}> / {agents.length} active</span>
          </div>
        </div>
      </div>

      {/* Grid */}
      <motion.div
        initial="hidden"
        animate="show"
        variants={{ show: { transition: { staggerChildren: 0.07 } } }}
        style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}
      >
        {agents.map(a => (
          <motion.div key={a.id} variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0, transition: { duration: 0.45, ease: [0.22, 1, 0.36, 1] } } }}>
            <AgentCard agent={a as typeof MOCK_AGENTS[0]} />
          </motion.div>
        ))}
      </motion.div>
    </motion.div>
  );
}
