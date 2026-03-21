"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import {
  motion,
  useInView,
  useMotionValue,
  useSpring,
  useScroll,
  useTransform,
  AnimatePresence,
} from "framer-motion";

/* ─── Gradient text helper ─── */
const GRAD = {
  background: "linear-gradient(135deg, #7C3AED, #A855F7, #C084FC)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

/* ─── Animated counter ─── */
function Counter({
  to,
  decimals = 0,
  prefix = "",
  suffix = "",
  delay = 0,
}: {
  to: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const v = useMotionValue(0);
  const spring = useSpring(v, { stiffness: 50, damping: 18 });
  const [display, setDisplay] = useState("0");

  useEffect(() => {
    if (inView) {
      const timer = setTimeout(() => v.set(to), delay);
      return () => clearTimeout(timer);
    }
  }, [inView, to, v, delay]);

  useEffect(() => spring.on("change", val => setDisplay(val.toFixed(decimals))), [spring, decimals]);

  return (
    <span ref={ref}>
      {prefix}
      {display}
      {suffix}
    </span>
  );
}

/* ─── 3D tilt card ─── */
function TiltCard({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [6, -6]), { stiffness: 200, damping: 30 });
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-6, 6]), { stiffness: 200, damping: 30 });

  const handleMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const rect = ref.current?.getBoundingClientRect();
      if (!rect) return;
      x.set((e.clientX - rect.left) / rect.width - 0.5);
      y.set((e.clientY - rect.top) / rect.height - 0.5);
    },
    [x, y]
  );

  const handleLeave = useCallback(() => {
    x.set(0);
    y.set(0);
  }, [x, y]);

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: "preserve-3d",
        perspective: 800,
        ...style,
      }}
    >
      {children}
    </motion.div>
  );
}

/* ─── Data ─── */
const STATS = [
  { label: "Total Value Locked", value: 2.41, prefix: "$", suffix: "M", decimals: 2 },
  { label: "Accrued Yield", value: 10.08, prefix: "$", suffix: "", decimals: 2 },
  { label: "Protocol APY", value: 4.21, prefix: "", suffix: "%", decimals: 2 },
  { label: "Active Operators", value: 6, prefix: "", suffix: "", decimals: 0 },
];

const FLOW = [
  {
    step: "01",
    label: "Deposit ETH",
    body: "Stake ETH into the Lido vault via ERC-4626. Receive wstETH shares that compound automatically.",
    icon: "◈",
  },
  {
    step: "02",
    label: "Earn Yield",
    body: "wstETH accrues 4.2% APY. Yield accumulates in the treasury each epoch without intervention.",
    icon: "◆",
  },
  {
    step: "03",
    label: "Operators Act",
    body: "The keeper harvests yield and allocates compute budget to 6 specialized sub-agents.",
    icon: "⬡",
  },
  {
    step: "04",
    label: "Work & Earn",
    body: "Operators execute tasks, earn reputation, and re-stake rewards — indefinitely.",
    icon: "◎",
  },
];

const PRIMITIVES = [
  {
    accent: "#7C3AED",
    title: "Self-Funding",
    body: "Stakes ETH, earns wstETH yield, and uses that yield to pay for its own operations — no human top-ups.",
    tag: "ERC-4626",
  },
  {
    accent: "#F59E0B",
    title: "Agent Swarm",
    body: "Six specialized operators run in parallel — trading, staking, scoring, proving, keeping, monitoring.",
    tag: "MCP Protocol",
  },
  {
    accent: "#059669",
    title: "ZK Identity",
    body: "Every operator carries a ZK-verifiable identity via ERC-8004. Prove claims without revealing inputs.",
    tag: "ERC-8004",
  },
  {
    accent: "#0284C7",
    title: "Reputation Staking",
    body: "Operators stake to guarantee work. Slash quorum of 3-of-N removes bad actors. Rewards go to public goods.",
    tag: "EigenTrust",
  },
  {
    accent: "#DC2626",
    title: "x402 Payments",
    body: "Per-request micropayments settled onchain in milliseconds via HTTP 402 payment protocol.",
    tag: "HTTP 402",
  },
  {
    accent: "#7C3AED",
    title: "Multi-chain",
    body: "Mainnet for ERC-8004 and staking. Arbitrum for perps. Base for x402. Celo for mobile.",
    tag: "4 chains",
  },
];

const TERMINAL_LINES = [
  { agent: "keeper", color: "#A855F7", msg: "treasury_check → gas 20 gwei · threshold OK" },
  { agent: "monitor", color: "#7C3AED", msg: "vault_health → APY 4.2% · spread +40bps · hold" },
  { agent: "prover", color: "#C084FC", msg: "proof_generated → api_proof · 2.1 KB · 1.8s" },
  { agent: "trader", color: "#F59E0B", msg: "budget_allocated → 0.01 ETH · swap queued" },
  { agent: "staker", color: "#059669", msg: "yield_harvest → 0.0042 ETH → treasury" },
  { agent: "scorer", color: "#0284C7", msg: "impact_eval → DecentraSeed score=78/100" },
];

/* ─── Variants ─── */
const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
};
const stagger = { show: { transition: { staggerChildren: 0.1 } } };

/* ─── Types ─── */
interface TickerEntry {
  t: string;
  agent: string;
  action: string;
  result: string | Record<string, unknown>;
}

/* ─── Live ticker ─── */
function LiveTicker({ entries }: { entries: TickerEntry[] }) {
  const items = entries.slice(0, 20);
  const doubled = [...items, ...items];

  return (
    <div
      style={{
        overflow: "hidden",
        borderTop: "1px solid var(--border)",
        borderBottom: "1px solid var(--border)",
        background: "#FFFFFF",
        padding: "14px 0",
      }}
    >
      <div
        className="ticker"
        style={{
          display: "flex",
          gap: 0,
          whiteSpace: "nowrap",
          width: "max-content",
        }}
      >
        {doubled.map((e, i) => {
          const result =
            typeof e.result === "string"
              ? e.result.slice(0, 60)
              : `${e.action} completed`;
          return (
            <div
              key={i}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                padding: "0 32px",
                fontSize: 12,
                color: "var(--text-3)",
                borderRight: "1px solid var(--border)",
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: "#7C3AED",
                  display: "inline-block",
                  flexShrink: 0,
                }}
              />
              <span style={{ color: "#7C3AED", fontWeight: 700, fontFamily: "monospace" }}>
                [{e.t}]
              </span>
              <span style={{ fontWeight: 600, color: "var(--text-2)" }}>{e.agent}</span>
              <span style={{ color: "var(--text-3)" }}>→ {result}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Terminal ─── */
function HeroTerminal() {
  const [lineIndex, setLineIndex] = useState(0);
  const [visible, setVisible] = useState<typeof TERMINAL_LINES>([]);

  useEffect(() => {
    const id = setInterval(() => {
      setLineIndex(prev => {
        const next = (prev + 1) % TERMINAL_LINES.length;
        setVisible(v => {
          const updated = [...v, TERMINAL_LINES[next]];
          return updated.slice(-6);
        });
        return next;
      });
    }, 1400);
    setVisible(TERMINAL_LINES.slice(0, 4));
    return () => clearInterval(id);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 40, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.9, delay: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="terminal"
      style={{
        marginTop: 64,
        borderRadius: 16,
        padding: "0",
        width: "100%",
        maxWidth: 680,
        boxShadow: "0 2px 8px rgba(0,0,0,0.16), 0 32px 64px rgba(0,0,0,0.12)",
        overflow: "hidden",
      }}
    >
      {/* Terminal titlebar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "12px 18px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
          background: "#1A1A1A",
        }}
      >
        <div style={{ display: "flex", gap: 6 }}>
          {["#FF5F57", "#FFBD2E", "#28C840"].map(c => (
            <div
              key={c}
              style={{ width: 10, height: 10, borderRadius: "50%", background: c }}
            />
          ))}
        </div>
        <span
          style={{
            flex: 1,
            textAlign: "center",
            fontSize: 11,
            color: "#4B5563",
            fontFamily: "monospace",
          }}
        >
          nexus-agent — live session
        </span>
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "#28C840",
            display: "inline-block",
          }}
          className="pulse"
        />
      </div>

      {/* Terminal body */}
      <div
        style={{
          padding: "20px 22px",
          fontFamily: "monospace",
          fontSize: 12,
          lineHeight: 1.9,
          minHeight: 160,
        }}
      >
        <AnimatePresence initial={false}>
          {visible.map((line, i) => (
            <motion.div
              key={`${line.agent}-${i}`}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              style={{ display: "flex", gap: 10 }}
            >
              <span style={{ color: "#4B5563" }}>$</span>
              <span style={{ color: line.color, fontWeight: 700, minWidth: 64 }}>
                [{line.agent}]
              </span>
              <span style={{ color: "#9CA3AF" }}>{line.msg}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        <div
          style={{
            display: "inline-block",
            width: 8,
            height: 14,
            background: "#7C3AED",
            marginTop: 2,
            verticalAlign: "middle",
          }}
          className="pulse"
        />
      </div>
    </motion.div>
  );
}

/* ─── Main page ─── */
export default function LandingPage() {
  const [tickerEntries, setTickerEntries] = useState<TickerEntry[]>([]);
  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 500], [0, -80]);

  useEffect(() => {
    fetch("/api/agents")
      .then(r => r.json())
      .then(data => {
        // We'll use a synthesized ticker from agent names and actions
        if (data?.agents) {
          const synth: TickerEntry[] = data.agents.map(
            (a: { id: string; last_action: string; last_seen: string }) => ({
              t: a.last_seen ?? "00:00",
              agent: a.id,
              action: a.last_action,
              result: a.last_action,
            })
          );
          setTickerEntries(synth);
        }
      })
      .catch(() => {});

    // Also try to get raw entries from treasury for richer ticker
    fetch("/api/treasury")
      .then(r => r.json())
      .then(() => {})
      .catch(() => {});
  }, []);

  return (
    <div style={{ background: "var(--bg)", color: "var(--text)", minHeight: "100vh", overflowX: "hidden" }}>

      {/* ── HERO ── */}
      <section
        style={{
          position: "relative",
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "120px 24px 80px",
          overflow: "hidden",
        }}
      >
        {/* Soft background gradient blobs */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            pointerEvents: "none",
            zIndex: 0,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "5%",
              left: "50%",
              transform: "translateX(-50%)",
              width: 800,
              height: 500,
              background:
                "radial-gradient(ellipse at center, rgba(124,58,237,0.07) 0%, transparent 70%)",
              filter: "blur(40px)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: "40%",
              left: "10%",
              width: 400,
              height: 400,
              background:
                "radial-gradient(ellipse at center, rgba(245,158,11,0.05) 0%, transparent 70%)",
              filter: "blur(60px)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: "30%",
              right: "8%",
              width: 300,
              height: 300,
              background:
                "radial-gradient(ellipse at center, rgba(168,85,247,0.06) 0%, transparent 70%)",
              filter: "blur(40px)",
            }}
          />
        </div>

        <motion.div style={{ y: heroY, position: "relative", zIndex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
          {/* Live badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 16px 6px 10px",
              borderRadius: 100,
              border: "1px solid rgba(124,58,237,0.2)",
              background: "rgba(124,58,237,0.06)",
              marginBottom: 36,
              cursor: "default",
            }}
          >
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                background: "#7C3AED",
                display: "inline-block",
              }}
              className="pulse"
            />
            <span style={{ fontSize: 12, color: "#7C3AED", fontWeight: 600 }}>
              Live on Ethereum Mainnet
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            style={{
              fontSize: "clamp(52px, 7.5vw, 96px)",
              fontWeight: 900,
              letterSpacing: "-0.045em",
              lineHeight: 1.02,
              margin: "0 0 28px",
              maxWidth: 960,
              color: "#0F0F0F",
            }}
          >
            The protocol that{" "}
            <span style={GRAD}>funds itself</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.22, ease: [0.22, 1, 0.36, 1] }}
            style={{
              fontSize: "clamp(17px, 2vw, 21px)",
              color: "#6B7280",
              maxWidth: 520,
              lineHeight: 1.65,
              marginBottom: 48,
            }}
          >
            Nexus stakes ETH, earns wstETH yield, and uses that yield to pay for its own
            on-chain operations — indefinitely.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.34 }}
            style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center" }}
          >
            <Link href="/dashboard" style={{ textDecoration: "none" }}>
              <motion.button
                whileHover={{ scale: 1.04, boxShadow: "0 8px 32px rgba(124,58,237,0.28)" }}
                whileTap={{ scale: 0.97 }}
                style={{
                  padding: "14px 32px",
                  borderRadius: 12,
                  background: "linear-gradient(135deg, #7C3AED, #A855F7)",
                  border: "none",
                  color: "#FFFFFF",
                  fontSize: 15,
                  fontWeight: 700,
                  cursor: "pointer",
                  letterSpacing: "-0.01em",
                  boxShadow: "0 4px 16px rgba(124,58,237,0.22)",
                  transition: "box-shadow 0.2s",
                }}
              >
                Open App →
              </motion.button>
            </Link>
            <a href="https://github.com" target="_blank" rel="noopener" style={{ textDecoration: "none" }}>
              <motion.button
                whileHover={{ scale: 1.03, background: "rgba(0,0,0,0.04)" }}
                whileTap={{ scale: 0.97 }}
                style={{
                  padding: "14px 32px",
                  borderRadius: 12,
                  background: "transparent",
                  border: "1px solid rgba(0,0,0,0.1)",
                  color: "#374151",
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "background 0.15s",
                }}
              >
                View on GitHub
              </motion.button>
            </a>
          </motion.div>

          {/* Terminal */}
          <HeroTerminal />
        </motion.div>
      </section>

      {/* ── LIVE TICKER ── */}
      {tickerEntries.length > 0 && <LiveTicker entries={tickerEntries} />}

      {/* ── STATS BAR ── */}
      <section style={{ padding: "80px 24px", maxWidth: 1120, margin: "0 auto" }}>
        <motion.div
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4,1fr)",
            gap: 0,
            borderRadius: 20,
            overflow: "hidden",
            border: "1px solid var(--border)",
            boxShadow: "var(--shadow-card)",
            background: "#FFFFFF",
          }}
        >
          {STATS.map((s, i) => (
            <motion.div
              key={s.label}
              variants={fadeUp}
              style={{
                padding: "36px 32px",
                textAlign: "center",
                borderRight: i < STATS.length - 1 ? "1px solid var(--border)" : "none",
              }}
            >
              <div
                style={{
                  fontSize: "clamp(32px, 4vw, 48px)",
                  fontWeight: 900,
                  letterSpacing: "-0.05em",
                  color: "#0F0F0F",
                  marginBottom: 8,
                }}
              >
                <Counter to={s.value} decimals={s.decimals} prefix={s.prefix} suffix={s.suffix} delay={i * 120} />
              </div>
              <div
                style={{
                  fontSize: 12,
                  color: "#9CA3AF",
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  fontWeight: 500,
                }}
              >
                {s.label}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section style={{ padding: "40px 24px 100px", maxWidth: 1120, margin: "0 auto" }}>
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55 }}
          style={{ textAlign: "center", marginBottom: 64 }}
        >
          <div
            style={{
              fontSize: 11,
              color: "#7C3AED",
              fontWeight: 700,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              marginBottom: 14,
            }}
          >
            How it works
          </div>
          <h2
            style={{
              fontSize: "clamp(32px, 4.5vw, 52px)",
              fontWeight: 900,
              letterSpacing: "-0.04em",
              color: "#0F0F0F",
              marginBottom: 16,
            }}
          >
            Yield-funded{" "}
            <span style={GRAD}>autonomy</span>
          </h2>
          <p style={{ fontSize: 17, color: "#6B7280", maxWidth: 400, margin: "0 auto" }}>
            One deposit. Infinite operation.
          </p>
        </motion.div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: 16,
            position: "relative",
          }}
        >
          {/* Connector */}
          <div
            style={{
              position: "absolute",
              top: 36,
              left: "12.5%",
              width: "75%",
              height: 1,
              background:
                "linear-gradient(90deg, transparent, rgba(124,58,237,0.25), rgba(168,85,247,0.25), transparent)",
              zIndex: 0,
            }}
          />

          {FLOW.map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 32 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.12, duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
              style={{ position: "relative", zIndex: 1, textAlign: "center", padding: "0 16px" }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: "50%",
                  background: "#FFFFFF",
                  border: "1px solid rgba(124,58,237,0.2)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  margin: "0 auto 24px",
                  boxShadow: "0 2px 12px rgba(124,58,237,0.12)",
                  fontSize: 22,
                }}
              >
                {item.icon}
              </div>
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  color: "#7C3AED",
                  fontFamily: "monospace",
                  letterSpacing: "0.04em",
                  marginBottom: 8,
                }}
              >
                STEP {item.step}
              </div>
              <div
                style={{
                  fontSize: 16,
                  fontWeight: 800,
                  color: "#0F0F0F",
                  marginBottom: 10,
                  letterSpacing: "-0.02em",
                }}
              >
                {item.label}
              </div>
              <div style={{ fontSize: 13, color: "#6B7280", lineHeight: 1.65 }}>{item.body}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── PROTOCOL PRIMITIVES ── */}
      <section
        style={{
          padding: "40px 24px 100px",
          maxWidth: 1120,
          margin: "0 auto",
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.55 }}
          style={{ textAlign: "center", marginBottom: 64 }}
        >
          <div
            style={{
              fontSize: 11,
              color: "#F59E0B",
              fontWeight: 700,
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              marginBottom: 14,
            }}
          >
            Protocol primitives
          </div>
          <h2
            style={{
              fontSize: "clamp(32px, 4.5vw, 52px)",
              fontWeight: 900,
              letterSpacing: "-0.04em",
              color: "#0F0F0F",
            }}
          >
            Built on{" "}
            <span style={GRAD}>open standards</span>
          </h2>
        </motion.div>

        <motion.div
          variants={stagger}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 16,
          }}
        >
          {PRIMITIVES.map((p) => (
            <TiltCard key={p.title}>
              <motion.div
                variants={fadeUp}
                whileHover={{ y: -6 }}
                style={{
                  background: "#FFFFFF",
                  border: "1px solid var(--border)",
                  borderRadius: 20,
                  padding: "28px 28px 30px",
                  cursor: "default",
                  boxShadow: "var(--shadow-card)",
                  transition: "box-shadow 0.25s",
                  height: "100%",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 18 }}>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 12,
                      background: `${p.accent}0F`,
                      border: `1px solid ${p.accent}22`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 20,
                    }}
                  >
                    <div style={{ width: 16, height: 16, borderRadius: "50%", background: p.accent, opacity: 0.8 }} />
                  </div>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      padding: "3px 8px",
                      borderRadius: 6,
                      background: `${p.accent}0F`,
                      color: p.accent,
                      fontFamily: "monospace",
                      letterSpacing: "0.02em",
                    }}
                  >
                    {p.tag}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 800,
                    color: "#0F0F0F",
                    marginBottom: 10,
                    letterSpacing: "-0.02em",
                  }}
                >
                  {p.title}
                </div>
                <div style={{ fontSize: 13.5, color: "#6B7280", lineHeight: 1.65 }}>{p.body}</div>
              </motion.div>
            </TiltCard>
          ))}
        </motion.div>
      </section>

      {/* ── CTA SECTION ── */}
      <section style={{ padding: "0 24px 100px", maxWidth: 1120, margin: "0 auto" }}>
        <motion.div
          initial={{ opacity: 0, y: 28 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          style={{
            background: "linear-gradient(135deg, #7C3AED 0%, #A855F7 50%, #C084FC 100%)",
            borderRadius: 28,
            padding: "80px 40px",
            textAlign: "center",
            position: "relative",
            overflow: "hidden",
          }}
        >
          {/* Inner glow */}
          <div
            style={{
              position: "absolute",
              top: "-40%",
              left: "50%",
              transform: "translateX(-50%)",
              width: "60%",
              height: "200%",
              background:
                "radial-gradient(ellipse at center, rgba(255,255,255,0.15) 0%, transparent 60%)",
              pointerEvents: "none",
            }}
          />

          <h2
            style={{
              fontSize: "clamp(28px, 4.5vw, 52px)",
              fontWeight: 900,
              letterSpacing: "-0.04em",
              color: "#FFFFFF",
              marginBottom: 18,
              position: "relative",
            }}
          >
            Start with one deposit
          </h2>
          <p
            style={{
              fontSize: 17,
              color: "rgba(255,255,255,0.75)",
              marginBottom: 44,
              maxWidth: 460,
              margin: "0 auto 44px",
              lineHeight: 1.65,
              position: "relative",
            }}
          >
            Connect your wallet, deposit ETH, and let Nexus run itself. Your principal stays
            safe. Yield does the work.
          </p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap", position: "relative" }}>
            <Link href="/dashboard" style={{ textDecoration: "none" }}>
              <motion.button
                whileHover={{ scale: 1.05, boxShadow: "0 8px 32px rgba(0,0,0,0.25)" }}
                whileTap={{ scale: 0.97 }}
                style={{
                  padding: "15px 40px",
                  borderRadius: 14,
                  background: "#FFFFFF",
                  border: "none",
                  color: "#7C3AED",
                  fontSize: 15,
                  fontWeight: 800,
                  cursor: "pointer",
                  letterSpacing: "-0.01em",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
                }}
              >
                Open App →
              </motion.button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ── FOOTER ── */}
      <footer
        style={{
          borderTop: "1px solid var(--border)",
          padding: "28px 40px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          maxWidth: 1120,
          margin: "0 auto",
        }}
      >
        <span style={{ fontSize: 15, fontWeight: 800, color: "#0F0F0F", letterSpacing: "-0.02em" }}>
          nexus<span style={{ color: "#7C3AED" }}>.</span>
        </span>
        <span style={{ fontSize: 12, color: "#9CA3AF" }}>
          Open source · ERC-8004 · ERC-4626 · Powered by wstETH
        </span>
        <span style={{ fontSize: 12, color: "#9CA3AF" }}>MIT License</span>
      </footer>
    </div>
  );
}
