'use client'
import React from 'react'

interface Budget { allocated: number; spent: number }
interface AgentData {
  id: string; status: string; budget: Budget
  last_action: string; cycles: number; uptime_seconds: number
}
interface Props { agent: AgentData; color: string }

const STATUS_COLORS: Record<string, string> = {
  running: '#34d399', idle: '#6b7280', paused: '#f59e0b', error: '#fb7185'
}

function fmtUptime(secs: number) {
  const h = Math.floor(secs / 3600), m = Math.floor((secs % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

export const AgentCard: React.FC<Props> = ({ agent, color }) => {
  const pct = agent.budget.allocated > 0 ? (agent.budget.spent / agent.budget.allocated) * 100 : 0
  const statusColor = STATUS_COLORS[agent.status] ?? '#6b7280'
  return (
    <div style={{ background: '#1e1e2e', border: `1px solid #313244`, borderRadius: 10, padding: 16, borderLeft: `3px solid ${color}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span style={{ fontWeight: 600, fontSize: 13, color }}>{agent.id}</span>
        <span style={{ fontSize: 11, background: statusColor + '22', color: statusColor, padding: '2px 8px', borderRadius: 20, fontWeight: 500 }}>
          {agent.status === 'running' && <span style={{ marginRight: 4 }}>●</span>}{agent.status}
        </span>
      </div>
      <div style={{ fontSize: 11, color: '#888', marginBottom: 8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {agent.last_action || 'No action yet'}
      </div>
      <div style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#666', marginBottom: 3 }}>
          <span>Budget</span><span>{agent.budget.spent.toFixed(4)} / {agent.budget.allocated.toFixed(4)} ETH</span>
        </div>
        <div style={{ height: 4, background: '#313244', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${Math.min(pct, 100)}%`, background: pct > 80 ? '#fb7185' : color, borderRadius: 2 }} />
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#555' }}>
        <span>{agent.cycles} cycles</span><span>↑ {fmtUptime(agent.uptime_seconds)}</span>
      </div>
    </div>
  )
}
