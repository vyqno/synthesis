import { NextResponse } from 'next/server'

const MOCK = [
  { id: 'nexus-trader', status: 'running', budget: { allocated: 0.05, spent: 0.012 }, last_action: 'DCA: 0.01 ETH @ $3,241', cycles: 47, uptime_seconds: 8040 },
  { id: 'nexus-staker', status: 'idle', budget: { allocated: 0.02, spent: 0.003 }, last_action: 'Wrapped 0.5 stETH → wstETH', cycles: 12, uptime_seconds: 8040 },
  { id: 'nexus-scorer', status: 'idle', budget: { allocated: 0.01, spent: 0.001 }, last_action: 'Scored: impact=82 legit=91', cycles: 5, uptime_seconds: 8040 },
  { id: 'nexus-keeper', status: 'running', budget: { allocated: 0.005, spent: 0 }, last_action: 'Gas 18 gwei — OK', cycles: 96, uptime_seconds: 8040 },
  { id: 'nexus-prover', status: 'idle', budget: { allocated: 0.005, spent: 0 }, last_action: 'Proof cached: api_proof', cycles: 3, uptime_seconds: 8040 },
  { id: 'nexus-monitor', status: 'idle', budget: { allocated: 0.002, spent: 0 }, last_action: 'EarnETH APY: 4.2%', cycles: 32, uptime_seconds: 8040 },
]

export async function GET() {
  return NextResponse.json(MOCK)
}
