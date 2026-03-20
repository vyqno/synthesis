'use client'
import { useEffect, useRef, useState } from 'react'

const AGENT_COLORS: Record<string, string> = {
  'nexus-trader': '#f59e0b', 'nexus-staker': '#34d399', 'nexus-scorer': '#60a5fa',
  'nexus-keeper': '#a78bfa', 'nexus-prover': '#fb7185', 'nexus-monitor': '#fbbf24',
  'nexus': '#6366f1',
}

const MOCK_EVENTS = [
  { t: Date.now()/1000 - 10, agent: 'nexus-keeper', action: 'treasury_check', result: { gas_gwei: 18.2, deferred: false } },
  { t: Date.now()/1000 - 65, agent: 'nexus-trader', action: 'price_check', result: { price: 3241.50, action: 'dca' } },
  { t: Date.now()/1000 - 130, agent: 'nexus-monitor', action: 'vault_health_check', result: { apy: 4.2, alert: false } },
  { t: Date.now()/1000 - 300, agent: 'nexus-staker', action: 'rebalance_check', result: { apy: 4.2, action: 'hold' } },
  { t: Date.now()/1000 - 500, agent: 'nexus-prover', action: 'generate_proof', result: { circuit: 'api_proof', cached: true } },
]

const MOCK_YIELD = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2,'0')}:00`,
  yield_eth: 0.0001 + Math.random() * 0.0003
}))

function YieldSparkline({ data }: { data: typeof MOCK_YIELD }) {
  const max = Math.max(...data.map(d => d.yield_eth))
  const min = Math.min(...data.map(d => d.yield_eth))
  const W = 200, H = 60
  const pts = data.map((d, i) => {
    const x = (i / (data.length - 1)) * W
    const y = H - ((d.yield_eth - min) / (max - min + 0.0001)) * H * 0.8 - 5
    return `${x},${y}`
  }).join(' ')
  const total = data.reduce((s, d) => s + d.yield_eth, 0)
  return (
    <div style={{ background: '#1e1e2e', border: '1px solid #313244', borderRadius: 12, padding: 16 }}>
      <div style={{ fontSize: 11, color: '#888', marginBottom: 8 }}>24h Yield Earned</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: '#6366f1', marginBottom: 12 }}>{(total * 1e6).toFixed(2)} μETH</div>
      <svg width={W} height={H} style={{ overflow: 'visible' }}>
        <polyline points={pts} fill="none" stroke="#6366f1" strokeWidth={2} strokeLinejoin="round" />
        <defs>
          <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={`0,${H} ${pts} ${W},${H}`} fill="url(#g)" />
      </svg>
    </div>
  )
}

export default function LivePage() {
  const [events, setEvents] = useState(MOCK_EVENTS)
  const [connected, setConnected] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    try {
      const es = new EventSource('/api/events')
      es.onopen = () => setConnected(true)
      es.onmessage = (e) => {
        const ev = JSON.parse(e.data)
        setEvents(prev => [ev, ...prev].slice(0, 100))
      }
      es.onerror = () => setConnected(false)
      return () => es.close()
    } catch { setConnected(false) }
  }, [])

  const fmt = (t: number) => new Date(t * 1000).toLocaleTimeString()

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>Live Agent Feed</h1>
        <span style={{ fontSize: 12, color: connected ? '#34d399' : '#f59e0b',
          background: connected ? '#34d39922' : '#f59e0b22', padding: '4px 10px', borderRadius: 12 }}>
          {connected ? '● Connected' : '○ Polling'}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 220px', gap: 24 }}>
        <div style={{ background: '#1e1e2e', border: '1px solid #313244', borderRadius: 12, overflow: 'hidden', maxHeight: 600, overflowY: 'auto' }}>
          {events.map((ev, i) => (
            <div key={i} style={{ display: 'grid', gridTemplateColumns: '80px 130px 140px 1fr',
              gap: 12, padding: '10px 16px', borderBottom: '1px solid #1a1a2a', alignItems: 'center',
              background: i === 0 ? '#252535' : 'transparent' }}>
              <span style={{ fontSize: 11, color: '#555', fontFamily: 'monospace' }}>{fmt(ev.t)}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: AGENT_COLORS[ev.agent] ?? '#888' }}>{ev.agent}</span>
              <span style={{ fontSize: 12, color: '#a0a0b8', fontFamily: 'monospace' }}>{ev.action}</span>
              <span style={{ fontSize: 11, color: '#666', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {JSON.stringify(ev.result)}
              </span>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <YieldSparkline data={MOCK_YIELD} />
      </div>
    </div>
  )
}
