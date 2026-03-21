import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

interface LogEntry {
  t: string
  agent: string
  action: string
  result: unknown
  tool?: string
}

interface AgentLog {
  agent: string
  session: string
  entries: LogEntry[]
}

export async function GET() {
  try {
    const logPath = path.join(process.cwd(), '..', 'agent_log.json')
    const raw: AgentLog = JSON.parse(fs.readFileSync(logPath, 'utf-8'))
    const entries = raw.entries ?? []

    // Derive per-agent stats from sub-agent action names like "nexus-trader.budget_allocated"
    const agentStats: Record<string, { cycles: number; lastAction: string; lastTime: string }> = {}

    for (const entry of entries) {
      // Extract sub-agent from action name if it contains "."
      const dotIdx = entry.action.indexOf('.')
      if (dotIdx > 0) {
        const subAgent = entry.action.slice(0, dotIdx)
        const action = entry.action.slice(dotIdx + 1)
        if (!agentStats[subAgent]) {
          agentStats[subAgent] = { cycles: 0, lastAction: action, lastTime: entry.t }
        }
        agentStats[subAgent].cycles++
        agentStats[subAgent].lastAction = action
        agentStats[subAgent].lastTime = entry.t
      }
    }

    // Also count direct agent entries (non-sub-agent)
    const nexusEntries = entries.filter(e => !e.action.includes('.'))
    const nexusCycles = nexusEntries.length
    const nexusLast = nexusEntries.at(-1)

    // Build agent list — always include all 6 sub-agents
    const SUB_AGENTS = [
      'nexus-trader',
      'nexus-staker',
      'nexus-scorer',
      'nexus-keeper',
      'nexus-prover',
      'nexus-monitor',
    ]

    const agents = SUB_AGENTS.map(id => {
      const stats = agentStats[id]
      const cycles = stats?.cycles ?? 0
      const lastAction = stats?.lastAction ?? 'awaiting task'
      const lastTime = stats?.lastTime ?? null

      // Status: active if seen in log, idle otherwise
      const status = stats ? 'running' : 'idle'

      return {
        id,
        status,
        cycles,
        last_action: lastAction,
        last_seen: lastTime,
        budget: {
          allocated: 0.01 * cycles || 0.01,
          spent: parseFloat((0.0008 * cycles).toFixed(4)),
        },
      }
    })

    return NextResponse.json({
      session: raw.session,
      total_entries: entries.length,
      nexus_cycles: nexusCycles,
      nexus_last_action: nexusLast?.action ?? 'none',
      agents,
    })
  } catch (e) {
    return NextResponse.json({ error: 'Could not read agent log', detail: String(e) }, { status: 500 })
  }
}
