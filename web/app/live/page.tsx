"use client";
import { useEffect, useRef, useState } from "react";

const COLORS: Record<string, string> = {
  "nexus-trader":  "#f59e0b",
  "nexus-staker":  "#34d399",
  "nexus-scorer":  "#60a5fa",
  "nexus-keeper":  "#818cf8",
  "nexus-prover":  "#fb7185",
  "nexus-monitor": "#2dd4bf",
  "nexus":         "#6366f1",
};

const LABELS: Record<string, string> = {
  "nexus-trader":  "Trader",
  "nexus-staker":  "Staker",
  "nexus-scorer":  "Scorer",
  "nexus-keeper":  "Keeper",
  "nexus-prover":  "Prover",
  "nexus-monitor": "Monitor",
};

const MOCK_EVENTS = [
  { t: Date.now()/1000 - 8,   agent: "nexus-keeper",  action: "gas_check",         result: { gwei: 18.2, ok: true } },
  { t: Date.now()/1000 - 62,  agent: "nexus-trader",  action: "dca_execute",        result: { eth: 0.01, price: 3241.5 } },
  { t: Date.now()/1000 - 128, agent: "nexus-monitor", action: "vault_health",       result: { apy: 4.21, alert: false } },
  { t: Date.now()/1000 - 290, agent: "nexus-staker",  action: "rebalance_check",    result: { apy: 4.21, action: "hold" } },
  { t: Date.now()/1000 - 490, agent: "nexus-prover",  action: "proof_generate",     result: { circuit: "api_proof", cached: true } },
  { t: Date.now()/1000 - 620, agent: "nexus-scorer",  action: "impact_eval",        result: { score: 82, sybil: 91 } },
  { t: Date.now()/1000 - 900, agent: "nexus-staker",  action: "stake",              result: { eth: 0.1, wsteth: 0.0942 } },
  { t: Date.now()/1000 - 1200, agent: "nexus-keeper", action: "yield_harvest",      result: { eth: 0.0042, usd: 10.08 } },
];

const YIELD_DATA = Array.from({ length: 24 }, (_, i) => ({
  h: i,
  v: 0.00008 + Math.sin(i * 0.4) * 0.00004 + Math.random() * 0.00003,
}));

function YieldChart({ data }: { data: typeof YIELD_DATA }) {
  const W = 280, H = 80;
  const max = Math.max(...data.map(d => d.v));
  const min = Math.min(...data.map(d => d.v));
  const range = max - min || 0.00001;

  const pts = data.map((d, i) => {
    const x = (i / (data.length - 1)) * W;
    const y = H - ((d.v - min) / range) * H * 0.75 - 8;
    return [x, y] as [number, number];
  });

  const polyline = pts.map(([x, y]) => `${x},${y}`).join(" ");
  const area = `0,${H} ${polyline} ${W},${H}`;
  const total = data.reduce((s, d) => s + d.v, 0);

  return (
    <div style={{
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "var(--radius-lg)",
      padding: 22,
    }}>
      <div style={{ fontSize: 11, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 4 }}>
        24h Yield
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, color: "var(--accent)", letterSpacing: "-0.02em", marginBottom: 2 }}>
        {(total * 1e6).toFixed(2)} μETH
      </div>
      <div style={{ fontSize: 11, color: "var(--text-3)", marginBottom: 16 }}>
        ≈ ${(total * 2410).toFixed(4)}
      </div>
      <svg width={W} height={H} style={{ display: "block", overflow: "visible" }}>
        <defs>
          <linearGradient id="yg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2dd4bf" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#2dd4bf" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={area} fill="url(#yg)" />
        <polyline points={polyline} fill="none" stroke="#2dd4bf" strokeWidth="1.5" strokeLinejoin="round" />
        {/* Last point dot */}
        <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="3" fill="#2dd4bf" />
      </svg>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--text-3)", marginTop: 8 }}>
        <span>00:00</span>
        <span>12:00</span>
        <span>now</span>
      </div>
    </div>
  );
}

function ResultPill({ result }: { result: Record<string, unknown> }) {
  const entries = Object.entries(result).slice(0, 2);
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {entries.map(([k, v]) => (
        <span key={k} style={{
          fontSize: 10, fontFamily: "monospace",
          padding: "2px 7px", borderRadius: 4,
          background: "var(--surface-3)",
          color: "var(--text-3)",
        }}>
          {k}={String(v)}
        </span>
      ))}
    </div>
  );
}

export default function LivePage() {
  const [events, setEvents] = useState(MOCK_EVENTS);
  const [connected, setConnected] = useState(false);
  const [filter, setFilter] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      const es = new EventSource("/api/events");
      es.onopen = () => setConnected(true);
      es.onmessage = (e) => {
        const ev = JSON.parse(e.data);
        setEvents(prev => [ev, ...prev].slice(0, 200));
      };
      es.onerror = () => setConnected(false);
      return () => es.close();
    } catch { setConnected(false); }
  }, []);

  const fmt = (t: number) => new Date(t * 1000).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });

  const agents = [...new Set(MOCK_EVENTS.map(e => e.agent))];
  const displayed = filter ? events.filter(e => e.agent === filter) : events;

  return (
    <div style={{ padding: "92px 28px 60px", maxWidth: 1200, margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", color: "var(--text)", marginBottom: 4 }}>
            Activity
          </h1>
          <p style={{ fontSize: 13, color: "var(--text-3)" }}>
            Real-time protocol event stream — every on-chain and off-chain action.
          </p>
        </div>
        <span style={{
          fontSize: 11, fontWeight: 600,
          padding: "5px 12px", borderRadius: 20,
          background: connected ? "var(--green-dim)" : "var(--yellow-dim)",
          color: connected ? "var(--green)" : "var(--yellow)",
          border: `1px solid ${connected ? "rgba(52,211,153,0.15)" : "rgba(251,191,36,0.15)"}`,
          display: "flex", alignItems: "center", gap: 5,
        }}>
          <span className={connected ? "pulse" : ""} style={{
            width: 5, height: 5, borderRadius: "50%",
            background: connected ? "var(--green)" : "var(--yellow)",
            display: "inline-block",
          }} />
          {connected ? "Live stream" : "Polling"}
        </span>
      </div>

      {/* Filter bar */}
      <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
        <button
          onClick={() => setFilter(null)}
          style={{
            fontSize: 11, fontWeight: filter === null ? 600 : 400,
            padding: "4px 12px", borderRadius: 20,
            background: filter === null ? "rgba(45,212,191,0.12)" : "var(--surface)",
            color: filter === null ? "var(--accent)" : "var(--text-3)",
            border: `1px solid ${filter === null ? "rgba(45,212,191,0.25)" : "var(--border)"}`,
            cursor: "pointer",
          }}
        >All</button>
        {agents.map(agent => {
          const color = COLORS[agent] ?? "#818cf8";
          const active = filter === agent;
          return (
            <button
              key={agent}
              onClick={() => setFilter(active ? null : agent)}
              style={{
                fontSize: 11, fontWeight: active ? 600 : 400,
                padding: "4px 12px", borderRadius: 20,
                background: active ? `${color}15` : "var(--surface)",
                color: active ? color : "var(--text-3)",
                border: `1px solid ${active ? `${color}30` : "var(--border)"}`,
                cursor: "pointer",
              }}
            >
              {LABELS[agent] ?? agent}
            </button>
          );
        })}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 16, alignItems: "start" }}>

        {/* Event stream */}
        <div style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-lg)",
          overflow: "hidden",
          maxHeight: 600,
          overflowY: "auto",
        }}>
          {/* Table header */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "70px 100px 160px 1fr",
            gap: 12,
            padding: "10px 18px",
            borderBottom: "1px solid var(--border)",
            background: "var(--surface-2)",
          }}>
            {["Time", "Operator", "Action", "Result"].map(h => (
              <span key={h} style={{ fontSize: 10, fontWeight: 500, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.06em" }}>{h}</span>
            ))}
          </div>

          {displayed.map((ev, i) => {
            const color = COLORS[ev.agent] ?? "#818cf8";
            return (
              <div
                key={i}
                className={i === 0 ? "fade-in" : ""}
                style={{
                  display: "grid",
                  gridTemplateColumns: "70px 100px 160px 1fr",
                  gap: 12,
                  padding: "11px 18px",
                  borderBottom: "1px solid var(--border)",
                  alignItems: "center",
                  background: i === 0 ? "rgba(45,212,191,0.03)" : "transparent",
                }}
              >
                <span style={{ fontSize: 11, color: "var(--text-3)", fontFamily: "monospace" }}>{fmt(ev.t)}</span>
                <span style={{ fontSize: 12, fontWeight: 600, color }}>
                  {LABELS[ev.agent] ?? ev.agent}
                </span>
                <span style={{
                  fontSize: 11, fontFamily: "monospace",
                  color: "var(--text-2)",
                  padding: "2px 7px",
                  background: `${color}0d`,
                  borderRadius: 4,
                  display: "inline-block",
                }}>
                  {ev.action}
                </span>
                <ResultPill result={ev.result as Record<string, unknown>} />
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>

        {/* Right: yield chart + event count */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <YieldChart data={YIELD_DATA} />

          <div style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            padding: 20,
          }}>
            <div style={{ fontSize: 11, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 14 }}>
              Session Stats
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { k: "Events", v: String(events.length) },
                { k: "Gas spent", v: "0.00041 ETH" },
                { k: "Yield earned", v: "0.0042 ETH" },
                { k: "Uptime", v: "2h 14m" },
              ].map(r => (
                <div key={r.k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
                  <span style={{ color: "var(--text-3)" }}>{r.k}</span>
                  <span style={{ color: "var(--text-2)", fontWeight: 600, fontFamily: "monospace" }}>{r.v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
