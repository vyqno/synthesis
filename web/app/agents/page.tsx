'use client'
import { useEffect, useState } from 'react'

const AGENT_COLORS: Record<string, string> = {
  'nexus-trader': '#f59e0b',
  'nexus-staker': '#34d399',
  'nexus-scorer': '#60a5fa',
  'nexus-keeper': '#a78bfa',
  'nexus-prover': '#fb7185',
  'nexus-monitor': '#fbbf24',
}

const MOCK_AGENTS = [
  { id: 'nexus-trader', status: 'running', budget: { allocated: 0.05, spent: 0.012 }, last_action: 'DCA: 0.01 ETH @ $3,241', cycles: 47, uptime_seconds: 8040 },
  { id: 'nexus-staker', status: 'idle', budget: { allocated: 0.02, spent: 0.003 }, last_action: 'Wrapped 0.5 stETH → wstETH', cycles: 12, uptime_seconds: 8040 },
  { id: 'nexus-scorer', status: 'idle', budget: { allocated: 0.01, spent: 0.001 }, last_action: 'Scored project: impact=82, legit=91', cycles: 5, uptime_seconds: 8040 },
  { id: 'nexus-keeper', status: 'running', budget: { allocated: 0.005, spent: 0.0 }, last_action: 'Gas: 18 gwei — OK to transact', cycles: 96, uptime_seconds: 8040 },
  { id: 'nexus-prover', status: 'idle', budget: { allocated: 0.005, spent: 0.0 }, last_action: 'Proof cached: api_proof (sha256)', cycles: 3, uptime_seconds: 8040 },
  { id: 'nexus-monitor', status: 'idle', budget: { allocated: 0.002, spent: 0.0 }, last_action: 'EarnETH APY: 4.2% — no alert', cycles: 32, uptime_seconds: 8040 },
]

function formatUptime(secs: number) {
  const h = Math.floor(secs / 3600)
  const m = Math.floor((secs % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: '#34d399', idle: '#6b7280', paused: '#f59e0b', error: '#ef4444'
  }
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 12,
      color: colors[status] ?? '#6b7280', background: `${colors[status] ?? '#6b7280'}22`,
      padding: '2px 8px', borderRadius: 12, fontWeight: 600 }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: colors[status],
        animation: status === 'running' ? 'pulse 1.5s infinite' : 'none' }} />
      {status}
    </span>
  )
}

function AgentCard({ agent }: { agent: typeof MOCK_AGENTS[0] }) {
  const color = AGENT_COLORS[agent.id] ?? '#6366f1'
  const budgetPct = agent.budget.allocated > 0 ? (agent.budget.spent / agent.budget.allocated) * 100 : 0
  return (
    <div style={{ background: '#1e1e2e', border: `1px solid #313244`, borderRadius: 12,
      padding: 20, borderTop: `3px solid ${color}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontWeight: 700, color, fontSize: 14 }}>{agent.id}</span>
        <StatusBadge status={agent.status} />
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#888', marginBottom: 4 }}>
          <span>Budget</span>
          <span>{(agent.budget.spent * 1000).toFixed(2)}m / {(agent.budget.allocated * 1000).toFixed(2)}m ETH</span>
        </div>
        <div style={{ height: 4, background: '#313244', borderRadius: 2 }}>
          <div style={{ height: '100%', width: `${budgetPct}%`, background: color, borderRadius: 2, transition: 'width 0.3s' }} />
        </div>
      </div>
      <div style={{ fontSize: 11, color: '#888', marginBottom: 8 }}>
        <span style={{ color: '#ccc', fontSize: 12 }}>{agent.last_action}</span>
      </div>
      <div style={{ display: 'flex', gap: 16, fontSize: 11, color: '#666' }}>
        <span>{agent.cycles} cycles</span>
        <span>{formatUptime(agent.uptime_seconds)} uptime</span>
      </div>
    </div>
  )
}

export default function AgentsPage() {
  const [agents, setAgents] = useState(MOCK_AGENTS)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/agents').then(r => r.json()).then(data => {
      if (Array.isArray(data) && data.length > 0) setAgents(data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const anyRunning = agents.some(a => a.status === 'running')

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>Agent Swarm</h1>
        {anyRunning && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12,
            color: '#34d399', background: '#34d39922', padding: '4px 10px', borderRadius: 12 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#34d399',
              animation: 'pulse 1.5s infinite' }} />
            Live
          </span>
        )}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {agents.map(a => <AgentCard key={a.id} agent={a as typeof MOCK_AGENTS[0]} />)}
      </div>
      {loading && <div style={{ display: 'none' }} />}
      <style>{`@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }`}</style>
    </div>
  )
}
