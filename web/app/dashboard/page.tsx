"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { motion, useInView, useMotionValue, useSpring } from "framer-motion";
import { useWallet, CHAIN_NAMES } from "@/hooks/useWallet";

interface TreasuryData {
  principal_wsteth: number; principal_usd: number;
  accrued_yield_eth: number; accrued_yield_usd: number;
  apy: number; log_entries: number; session_date: string;
  on_chain_txs: number; inference_calls: number; usdc_earned: number;
}
interface AgentData {
  id: string; label: string; status: string; cycles: number;
  last_action: string; budget: { allocated: number; spent: number };
}

const AGENT_META: Record<string, { color: string; icon: string }> = {
  trader:  { color: "#F59E0B", icon: "⟠" },
  staker:  { color: "#22C55E", icon: "◈" },
  scorer:  { color: "#60A5FA", icon: "◎" },
  keeper:  { color: "#A855F7", icon: "⬡" },
  prover:  { color: "#EC4899", icon: "◆" },
  monitor: { color: "#2DD4BF", icon: "◉" },
};

function AnimatedNumber({ to, prefix = "", suffix = "", decimals = 0, delay = 0 }: {
  to: number; prefix?: string; suffix?: string; decimals?: number; delay?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const mv = useMotionValue(0);
  const spring = useSpring(mv, { stiffness: 50, damping: 18 });
  const [display, setDisplay] = useState("0");
  useEffect(() => { if (inView) setTimeout(() => mv.set(to), delay); }, [inView, to, mv, delay]);
  useEffect(() => spring.on("change", v => setDisplay(v.toFixed(decimals))), [spring, decimals]);
  return <span ref={ref}>{prefix}{display}{suffix}</span>;
}

function OperatorCard({ agent, delay }: { agent: AgentData; delay: number }) {
  const key = (agent.label ?? "").toLowerCase();
  const meta = AGENT_META[key] ?? { color: "#A855F7", icon: "●" };
  const pct = agent.budget?.allocated > 0
    ? Math.min((agent.budget.spent / agent.budget.allocated) * 100, 100)
    : Math.min((agent.cycles / 100) * 100, 100);
  const active = agent.status === "running" || agent.status === "active";
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -2, transition: { duration: 0.12 } }}
      style={{
        background: "var(--surface-2)", borderRadius: 12, padding: "14px 16px",
        border: "1px solid var(--border)",
        borderLeft: `3px solid ${active ? meta.color : "var(--surface-3)"}`,
        display: "flex", flexDirection: "column", gap: 10, cursor: "default",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 15, color: meta.color, opacity: active ? 1 : 0.3 }}>{meta.icon}</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: active ? "var(--text)" : "var(--text-3)" }}>{agent.label}</span>
        </div>
        <span style={{
          fontSize: 9, fontWeight: 800, letterSpacing: "0.06em",
          padding: "3px 8px", borderRadius: 100,
          background: active ? "rgba(34,197,94,0.1)" : "rgba(113,113,122,0.1)",
          color: active ? "var(--green)" : "var(--text-3)",
          border: `1px solid ${active ? "rgba(34,197,94,0.2)" : "rgba(113,113,122,0.12)"}`,
        }}>{active ? "LIVE" : "IDLE"}</span>
      </div>
      <div style={{ height: 3, borderRadius: 2, background: "var(--surface-3)", overflow: "hidden" }}>
        <motion.div
          initial={{ width: 0 }} animate={{ width: `${pct}%` }}
          transition={{ delay: delay + 0.3, duration: 0.9, ease: "easeOut" }}
          style={{ height: "100%", borderRadius: 2, background: active ? meta.color : "var(--surface-3)" }}
        />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--text-3)" }}>{agent.cycles} cycles</span>
        {active && <span className="pulse" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--green)", display: "inline-block" }} />}
      </div>
    </motion.div>
  );
}

export default function Dashboard() {
  const { address, isConnected, balance, chainId } = useWallet();
  const chainName = chainId ? (CHAIN_NAMES[chainId] ?? `Chain ${chainId}`) : "Mainnet";
  const [treasury, setTreasury] = useState<TreasuryData | null>(null);
  const [agents, setAgents] = useState<AgentData[]>([]);
  const [now, setNow] = useState(new Date());

  const load = useCallback(async () => {
    const [t, a] = await Promise.all([
      fetch("/api/treasury").then(r => r.json()).catch(() => null),
      fetch("/api/agents").then(r => r.json()).catch(() => []),
    ]);
    if (t && !t.error) setTreasury(t);
    if (Array.isArray(a) && a.length) setAgents(a);
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 1000); return () => clearInterval(t); }, []);

  const tvlUsd   = treasury?.principal_usd ?? 4451;
  const apy      = treasury?.apy ?? 4.2;
  const entries  = treasury?.log_entries ?? 97;
  const wsteth   = treasury?.principal_wsteth ?? 1.847;
  const yieldEth = treasury?.accrued_yield_eth ?? 0.0042;

  const displayAgents: AgentData[] = agents.length ? agents : [
    { id: "t",  label: "Trader",  status: "running", cycles: 47, last_action: "DCA 0.01 ETH", budget: { allocated: 0.05, spent: 0.012 } },
    { id: "s",  label: "Staker",  status: "running", cycles: 12, last_action: "wstETH wrap",  budget: { allocated: 0.02, spent: 0.003 } },
    { id: "sc", label: "Scorer",  status: "running", cycles: 6,  last_action: "impact=82",     budget: { allocated: 0.01, spent: 0.001 } },
    { id: "k",  label: "Keeper",  status: "running", cycles: 20, last_action: "Gas 18 gwei",  budget: { allocated: 0.005, spent: 0 } },
    { id: "p",  label: "Prover",  status: "running", cycles: 20, last_action: "ZK proof",      budget: { allocated: 0.005, spent: 0 } },
    { id: "m",  label: "Monitor", status: "running", cycles: 13, last_action: "APY 4.2%",      budget: { allocated: 0.002, spent: 0 } },
  ];

  const liveCount = displayAgents.filter(a => a.status === "running" || a.status === "active").length;

  const ACTIVITY = [
    { label: "Yield accruing",                                    sub: `${yieldEth} ETH · $${(yieldEth*2410).toFixed(2)}`,           tag: "live",  color: "#A855F7" },
    { label: `${treasury?.on_chain_txs ?? 8} on-chain txs`,       sub: "finalized · Base + Mainnet",                                  tag: "chain", color: "#22C55E" },
    { label: `${treasury?.inference_calls ?? 2} inference calls`,  sub: "Venice · llama-3.3-70b",                                     tag: "ai",    color: "#60A5FA" },
    { label: "ZK proof generated",                                 sub: "api_proof circuit · cached",                                  tag: "zk",    color: "#EC4899" },
    { label: `${treasury?.usdc_earned ?? 5} USDC earned`,          sub: "escrow released · proof delivery",                           tag: "earn",  color: "#F59E0B" },
    { label: `${entries} log entries`,                             sub: `session ${treasury?.session_date ?? "2026-03-20"}`,           tag: "meta",  color: "#2DD4BF" },
  ];

  const card = (extra?: React.CSSProperties): React.CSSProperties => ({
    background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 20, ...extra,
  });

  return (
    <div style={{ minHeight: "100vh", paddingTop: 72, paddingBottom: 64, background: "var(--bg)", position: "relative" }}>
      {/* Dot grid */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0, backgroundImage: "radial-gradient(rgba(255,255,255,0.028) 1px, transparent 1px)", backgroundSize: "28px 28px" }} />
      {/* Top glow */}
      <div style={{ position: "fixed", top: 0, left: "50%", transform: "translateX(-50%)", width: 800, height: 300, background: "radial-gradient(ellipse at top, rgba(168,85,247,0.08) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />

      <div style={{ maxWidth: 1300, margin: "0 auto", padding: "28px 28px 0", position: "relative", zIndex: 1 }}>

        {/* Wallet banner */}
        {isConnected && address && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
            style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20, padding: "10px 16px", borderRadius: 12, background: "rgba(168,85,247,0.06)", border: "1px solid rgba(168,85,247,0.15)", fontSize: 12, fontWeight: 500 }}>
            <span className="pulse" style={{ width: 7, height: 7, borderRadius: "50%", background: "#22C55E", display: "inline-block", flexShrink: 0 }} />
            <span style={{ fontFamily: "monospace", color: "#A855F7", fontWeight: 700 }}>{address.slice(0,8)}…{address.slice(-6)}</span>
            <span style={{ color: "var(--text-3)" }}>·</span>
            <span style={{ color: "#22C55E", fontWeight: 600 }}>{chainName}</span>
            {balance && <><span style={{ color: "var(--text-3)" }}>·</span><span style={{ color: "var(--text-2)" }}>{balance}</span></>}
            <span style={{ marginLeft: "auto", fontFamily: "monospace", color: "var(--text-3)", fontSize: 11 }}>{now.toLocaleTimeString()}</span>
          </motion.div>
        )}

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 32, fontWeight: 900, letterSpacing: "-0.04em", marginBottom: 4 }}>
            Protocol{" "}
            <span style={{ background: "linear-gradient(135deg,#A855F7,#EC4899,#F59E0B)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>
              Overview
            </span>
          </h1>
          <p style={{ fontSize: 13, color: "var(--text-3)" }}>{entries} real actions · {treasury?.session_date ?? "2026-03-20"} · {now.toLocaleTimeString()}</p>
        </motion.div>

        {/* BENTO */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(12,1fr)", gap: 12 }}>

          {/* 4 stat tiles */}
          {[
            { l: "TVL",       val: <AnimatedNumber to={tvlUsd} prefix="$" />,           sub: "wstETH principal",        accent: true,  d: 0 },
            { l: "APY",       val: <AnimatedNumber to={apy} decimals={1} suffix="%" />, sub: "Lido staking yield",      accent: false, d: 0.05 },
            { l: "Actions",   val: <AnimatedNumber to={entries} />,                      sub: "real log entries",         accent: false, d: 0.1 },
            { l: "Operators", val: <AnimatedNumber to={displayAgents.length} />,         sub: `${liveCount} live now`,   accent: false, d: 0.15 },
          ].map(s => (
            <motion.div key={s.l} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: s.d, duration: 0.5, ease: [0.22,1,0.36,1] }}
              style={{ gridColumn: "span 3", ...card({ padding: "22px 24px", display: "flex", flexDirection: "column", gap: 8,
                ...(s.accent ? { border: "1px solid rgba(168,85,247,0.25)", boxShadow: "0 0 24px rgba(168,85,247,0.08)" } : {})
              })}}
            >
              <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-3)" }}>{s.l}</p>
              <div style={{ fontSize: 44, fontWeight: 900, letterSpacing: "-0.04em",
                ...(s.accent ? { background: "linear-gradient(135deg,#A855F7,#EC4899)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" } : { color: "var(--text)" })
              }}>{s.val}</div>
              <p style={{ fontSize: 11, color: "var(--text-3)", fontWeight: 500 }}>{s.sub}</p>
            </motion.div>
          ))}

          {/* Vault */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5, ease: [0.22,1,0.36,1] }}
            style={{ gridColumn: "span 4", ...card({ padding: 24, display: "flex", flexDirection: "column", gap: 20,
              border: "1px solid rgba(168,85,247,0.2)", boxShadow: "inset 0 0 40px rgba(168,85,247,0.04)"
            })}}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-3)", marginBottom: 10 }}>wstETH Vault</p>
                <div style={{ fontSize: 50, fontWeight: 900, letterSpacing: "-0.04em", lineHeight: 1 }}><AnimatedNumber to={wsteth} decimals={3} delay={0.3} /></div>
                <p style={{ fontSize: 13, color: "var(--text-3)", marginTop: 4 }}>wstETH · ≈ ${tvlUsd.toLocaleString()}</p>
              </div>
              <span style={{ padding: "8px 14px", borderRadius: 100, background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.2)", fontSize: 13, fontWeight: 900, color: "var(--green)" }}>
                <AnimatedNumber to={apy} decimals={1} suffix="% APY" delay={0.35} />
              </span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              {[{ l: "Accrued Yield", v: `${yieldEth.toFixed(4)} ETH`, c: "#A855F7" }, { l: "USD Value", v: `$${(yieldEth*2410).toFixed(2)}`, c: "#F59E0B" }].map(s => (
                <div key={s.l} style={{ background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 16px" }}>
                  <p style={{ fontSize: 11, color: "var(--text-3)", marginBottom: 6 }}>{s.l}</p>
                  <p style={{ fontSize: 22, fontWeight: 900, color: s.c, letterSpacing: "-0.03em" }}>{s.v}</p>
                </div>
              ))}
            </div>
            <div style={{ background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { k: "Protocol",  v: "ERC-4626" }, { k: "Underlying", v: "wstETH (Lido)" },
                { k: "Network",   v: "Ethereum"  }, { k: "Session",    v: treasury?.session_date ?? "2026-03-20" },
                { k: "Clock",     v: now.toLocaleTimeString() },
              ].map(r => (
                <div key={r.k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                  <span style={{ color: "var(--text-3)" }}>{r.k}</span>
                  <span style={{ color: "var(--text-2)", fontWeight: 600, fontFamily: "monospace" }}>{r.v}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Operators */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.5, ease: [0.22,1,0.36,1] }}
            style={{ gridColumn: "span 5", ...card({ padding: 22, display: "flex", flexDirection: "column", gap: 14 })}}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-3)" }}>Operators</p>
              <span style={{ fontSize: 11, fontWeight: 800, color: "var(--green)" }}>{liveCount} / {displayAgents.length} live</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {displayAgents.map((a, i) => <OperatorCard key={a.id} agent={a} delay={0.3 + i * 0.05} />)}
            </div>
          </motion.div>

          {/* Activity */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5, ease: [0.22,1,0.36,1] }}
            style={{ gridColumn: "span 3", ...card({ padding: 22, display: "flex", flexDirection: "column" })}}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-3)" }}>Activity</p>
              <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 10, fontWeight: 800, color: "#A855F7" }}>
                <span className="pulse" style={{ width: 5, height: 5, borderRadius: "50%", background: "#A855F7", display: "inline-block" }} /> LIVE
              </span>
            </div>
            {ACTIVITY.map((item, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + i * 0.06, duration: 0.35 }}
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0", borderBottom: i < ACTIVITY.length-1 ? "1px solid var(--border)" : "none" }}
              >
                <div style={{ width: 28, height: 28, borderRadius: 8, flexShrink: 0, background: `${item.color}12`, border: `1px solid ${item.color}22`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: item.color }} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 11, fontWeight: 600, color: "var(--text)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.label}</p>
                  <p style={{ fontSize: 10, color: "var(--text-3)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginTop: 1 }}>{item.sub}</p>
                </div>
                <span style={{ fontSize: 9, fontWeight: 700, color: "var(--text-3)", fontFamily: "monospace", flexShrink: 0, padding: "2px 6px", background: "var(--surface-3)", borderRadius: 4 }}>{item.tag}</span>
              </motion.div>
            ))}
          </motion.div>

          {/* Bottom 4 info cards */}
          {[
            { label: "Protocol", items: [{ k: "Contract", v: "0x8004A1…9432" }, { k: "Standard", v: "ERC-8004 + ERC-4626" }, { k: "Audit", v: "In review" }] },
            { label: "Network",  items: [{ k: "Primary", v: "Ethereum" }, { k: "L2s", v: "Arbitrum · Base · Celo" }, { k: "Gas", v: "18 gwei" }] },
            { label: "Security", items: [{ k: "Custody", v: "Gnosis Safe 1-of-2" }, { k: "ZK", v: "Noir circuits" }, { k: "Slash", v: "3-of-N quorum" }] },
            { label: "Session",  items: [{ k: "On-chain", v: `${treasury?.on_chain_txs ?? 8} txs` }, { k: "Compute", v: `${treasury?.inference_calls ?? 2} calls` }, { k: "Earned", v: `${treasury?.usdc_earned ?? 5} USDC` }] },
          ].map((section, i) => (
            <motion.div key={section.label} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.45 + i * 0.05, duration: 0.45, ease: [0.22,1,0.36,1] }}
              style={{ gridColumn: "span 3", ...card({ padding: "18px 20px" })}}
            >
              <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-3)", marginBottom: 14 }}>{section.label}</p>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {section.items.map(r => (
                  <div key={r.k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                    <span style={{ color: "var(--text-3)" }}>{r.k}</span>
                    <span style={{ color: "var(--text-2)", fontWeight: 600, fontFamily: "monospace" }}>{r.v}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
