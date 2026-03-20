import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    listings: [
      { agent_id: 'nexus-scorer', name: 'Nexus Scorer', capabilities: ['public_goods_eval', 'sybil_check'], price_eth: 0.0001, reputation: 82, availability: 'available' },
      { agent_id: 'nexus-prover', name: 'Nexus Prover', capabilities: ['zk_proof', 'lit_tee'], price_eth: 0.0005, reputation: 91, availability: 'available' },
      { agent_id: 'nexus-trader', name: 'Nexus Trader', capabilities: ['uniswap_swap', 'gmx_perps'], price_eth: 0.001, reputation: 74, availability: 'busy' },
      { agent_id: 'nexus-staker', name: 'Nexus Staker', capabilities: ['lido_stake', 'wsteth_wrap'], price_eth: 0.0002, reputation: 88, availability: 'available' },
    ],
    escrows: [
      { escrow_id: 'escrow_001', recipient: '0x1a2b...3c4d', amount_eth: 0.0005, description: 'ZK proof generation', status: 'pending', created_at: Math.floor(Date.now()/1000) - 120 },
    ],
    payments: [
      { type: 'x402', description: 'Bankr inference', amount_eth: 0.00002, success: true, ts: Math.floor(Date.now()/1000) - 300 },
      { type: 'escrow', description: 'ZK proof: api_proof', amount_eth: 0.0005, success: true, ts: Math.floor(Date.now()/1000) - 1800 },
    ]
  })
}
