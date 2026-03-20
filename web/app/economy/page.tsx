'use client'
import { useEffect, useState } from 'react'

const MOCK_LISTINGS = [
  { agent_id: 'nexus-scorer', name: 'Nexus Scorer', capabilities: ['public_goods_eval', 'sybil_check'], price_eth: 0.0001, reputation: 82, availability: 'available' },
  { agent_id: 'nexus-prover', name: 'Nexus Prover', capabilities: ['zk_proof', 'lit_tee'], price_eth: 0.0005, reputation: 91, availability: 'available' },
  { agent_id: 'nexus-trader', name: 'Nexus Trader', capabilities: ['uniswap_swap', 'gmx_perps'], price_eth: 0.001, reputation: 74, availability: 'busy' },
  { agent_id: 'nexus-staker', name: 'Nexus Staker', capabilities: ['lido_stake', 'wsteth_wrap'], price_eth: 0.0002, reputation: 88, availability: 'available' },
]

const MOCK_ESCROWS = [
  { escrow_id: 'escrow_0x1a2b_1773', recipient: '0x1a2b...3c4d', amount_eth: 0.0005, description: 'ZK proof generation', status: 'pending', created_at: Date.now() / 1000 - 120 },
  { escrow_id: 'escrow_0x5e6f_1772', recipient: '0x5e6f...7a8b', amount_eth: 0.0001, description: 'Public goods eval', status: 'released', created_at: Date.now() / 1000 - 3600 },
]

const MOCK_PAYMENTS = [
  { type: 'x402', description: 'Bankr inference', amount_eth: 0.00002, success: true, ts: Date.now() / 1000 - 300 },
  { type: 'escrow', description: 'ZK proof: api_proof', amount_eth: 0.0005, success: true, ts: Date.now() / 1000 - 1800 },
]

function ReputationBadge({ score }: { score: number }) {
  const tier = score >= 80 ? ['trusted', '#34d399'] : score >= 50 ? ['verified', '#60a5fa'] : ['basic', '#9ca3af']
  return <span style={{ fontSize: 11, color: tier[1], background: `${tier[1]}22`, padding: '2px 8px', borderRadius: 8, fontWeight: 600 }}>{tier[0]} {score}</span>
}

export default function EconomyPage() {
  const [data, setData] = useState({ listings: MOCK_LISTINGS, escrows: MOCK_ESCROWS, payments: MOCK_PAYMENTS })

  useEffect(() => {
    fetch('/api/economy').then(r => r.json()).then(d => {
      if (d.listings?.length) setData(d)
    }).catch(() => {})
  }, [])

  return (
    <div style={{ padding: '32px 40px', maxWidth: 1100, margin: '0 auto' }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32 }}>Agent Economy</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 24 }}>
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#a0a0b8' }}>Marketplace</h2>
          <div style={{ background: '#1e1e2e', border: '1px solid #313244', borderRadius: 12, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #313244' }}>
                  {['Agent', 'Capabilities', 'Price/call', 'Reputation', ''].map(h => (
                    <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#666', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.listings.map(a => (
                  <tr key={a.agent_id} style={{ borderBottom: '1px solid #313244' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600, color: '#e0e0f0' }}>{a.name}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {a.capabilities.map(c => <span key={c} style={{ fontSize: 10, background: '#313244', color: '#888', padding: '1px 6px', borderRadius: 4 }}>{c}</span>)}
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#f59e0b', fontFamily: 'monospace' }}>{(a.price_eth * 1e6).toFixed(1)}μETH</td>
                    <td style={{ padding: '12px 16px' }}><ReputationBadge score={a.reputation} /></td>
                    <td style={{ padding: '12px 16px' }}>
                      <button style={{ fontSize: 11, background: '#6366f1', color: '#fff', border: 'none',
                        padding: '4px 12px', borderRadius: 6, cursor: 'pointer', opacity: a.availability === 'available' ? 1 : 0.4 }}
                        disabled={a.availability !== 'available'}>Hire</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: '#a0a0b8' }}>Pending Escrows</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {data.escrows.filter(e => e.status === 'pending').map(e => (
                <div key={e.escrow_id} style={{ background: '#1e1e2e', border: '1px solid #313244', borderRadius: 8, padding: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, color: '#e0e0f0' }}>{e.description}</span>
                    <span style={{ fontSize: 12, color: '#f59e0b', fontFamily: 'monospace' }}>{(e.amount_eth * 1e6).toFixed(1)}μETH</span>
                  </div>
                  <div style={{ fontSize: 11, color: '#666' }}>{e.recipient}</div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: '#a0a0b8' }}>Payment History</h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {data.payments.map((p, i) => (
                <div key={i} style={{ background: '#1e1e2e', border: '1px solid #313244', borderRadius: 8, padding: '8px 12px',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: 11, color: p.type === 'x402' ? '#60a5fa' : '#a78bfa',
                      background: p.type === 'x402' ? '#60a5fa22' : '#a78bfa22', padding: '1px 6px', borderRadius: 4, marginRight: 8 }}>{p.type}</span>
                    <span style={{ fontSize: 12, color: '#ccc' }}>{p.description}</span>
                  </div>
                  <span style={{ fontSize: 12, color: '#34d399', fontFamily: 'monospace' }}>{(p.amount_eth * 1e6).toFixed(1)}μETH</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
