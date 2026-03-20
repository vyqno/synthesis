'use client'
import React, { useEffect, useRef, useState } from 'react'

interface Event { t: number; agent: string; action: string; result: any }

const AGENT_COLORS: Record<string, string> = {
  'nexus-trader': '#f59e0b', 'nexus-staker': '#34d399', 'nexus-scorer': '#60a5fa',
  'nexus-keeper': '#a78bfa', 'nexus-prover': '#fb7185', 'nexus-monitor': '#fbbf24',
}

export const LiveFeed: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [connected, setConnected] = useState(false)
  const ref = useRef<EventSource | null>(null)

  useEffect(() => {
    const es = new EventSource('/api/events')
    ref.current = es
    es.onopen = () => setConnected(true)
    es.onmessage = (e) => {
      try {
        const evt = JSON.parse(e.data)
        setEvents(prev => [evt, ...prev].slice(0, 100))
      } catch {}
    }
    es.onerror = () => setConnected(false)
    return () => es.close()
  }, [])

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: connected ? '#34d399' : '#fb7185', display: 'inline-block' }} />
        <span style={{ fontSize: 11, color: connected ? '#34d399' : '#fb7185' }}>{connected ? 'Connected' : 'Reconnecting...'}</span>
      </div>
      <div style={{ maxHeight: 400, overflowY: 'auto' }}>
        {events.length === 0 && <div style={{ color: '#555', fontSize: 12 }}>Waiting for events...</div>}
        {events.map((e, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '80px 100px 120px 1fr', gap: 8, padding: '4px 0', borderBottom: '1px solid #1a1a2e', fontSize: 11, fontFamily: 'monospace' }}>
            <span style={{ color: '#555' }}>{new Date(e.t * 1000).toLocaleTimeString()}</span>
            <span style={{ color: AGENT_COLORS[e.agent] ?? '#888' }}>{e.agent?.replace('nexus-', '')}</span>
            <span style={{ color: '#ccc' }}>{e.action}</span>
            <span style={{ color: '#666', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {typeof e.result === 'object' ? JSON.stringify(e.result).slice(0, 60) : String(e.result)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
