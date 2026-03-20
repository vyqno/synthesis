'use client'
import React from 'react'

interface Payment { type: string; url?: string; amount: number; description: string; success: boolean; ts: number }
interface Escrow { escrow_id: string; recipient: string; amount_eth: number; status: string; created_at: number }
interface Props { payments: Payment[]; escrows: Escrow[] }

export const EconomyFeed: React.FC<Props> = ({ payments, escrows }) => (
  <div>
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Pending Escrows</div>
      {escrows.length === 0 && <div style={{ color: '#555', fontSize: 12 }}>No pending escrows</div>}
      {escrows.map(e => (
        <div key={e.escrow_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #1a1a2e', fontSize: 12 }}>
          <span style={{ color: '#888', fontFamily: 'monospace' }}>{e.escrow_id.slice(0, 20)}…</span>
          <span style={{ color: '#f59e0b' }}>{e.amount_eth.toFixed(4)} ETH</span>
          <span style={{ color: e.status === 'released' ? '#34d399' : '#6366f1' }}>{e.status}</span>
        </div>
      ))}
    </div>
    <div>
      <div style={{ fontSize: 11, color: '#888', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>Payment History</div>
      {payments.length === 0 && <div style={{ color: '#555', fontSize: 12 }}>No payments yet</div>}
      {payments.slice(-10).reverse().map((p, i) => (
        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #1a1a2e', fontSize: 12 }}>
          <span style={{ color: p.type === 'x402' ? '#60a5fa' : '#a78bfa' }}>{p.type}</span>
          <span style={{ color: '#ccc' }}>{p.description?.slice(0, 24)}</span>
          <span style={{ color: p.success ? '#34d399' : '#fb7185' }}>{p.success ? '+' : '✗'} {p.amount.toFixed(5)} ETH</span>
        </div>
      ))}
    </div>
  </div>
)
