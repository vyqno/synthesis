'use client'
import React from 'react'
import { AgentCard } from './AgentCard'

const AGENT_COLORS: Record<string, string> = {
  'nexus-trader': '#f59e0b', 'nexus-staker': '#34d399', 'nexus-scorer': '#60a5fa',
  'nexus-keeper': '#a78bfa', 'nexus-prover': '#fb7185', 'nexus-monitor': '#fbbf24',
}

interface Props { agents: any[] }

export const SubAgentGrid: React.FC<Props> = ({ agents }) => (
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
    {agents.map(a => (
      <AgentCard key={a.id} agent={a} color={AGENT_COLORS[a.id] ?? '#6366f1'} />
    ))}
  </div>
)
