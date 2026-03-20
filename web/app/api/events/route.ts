import * as fs from 'fs'
import * as path from 'path'

const LOG_PATH = path.join(process.cwd(), '..', 'agent_log.json')

const MOCK_EVENTS = [
  { t: Math.floor(Date.now()/1000) - 10, agent: 'nexus-keeper', action: 'treasury_check', result: { gas_gwei: 18.2 } },
  { t: Math.floor(Date.now()/1000) - 65, agent: 'nexus-trader', action: 'price_check', result: { price: 3241.5 } },
]

function readLog(): object[] {
  try {
    const raw = fs.readFileSync(LOG_PATH, 'utf-8')
    return raw.trim().split('\n').filter(Boolean).map(l => JSON.parse(l)).slice(-50)
  } catch {
    return MOCK_EVENTS
  }
}

export async function GET() {
  const encoder = new TextEncoder()
  let lastCount = 0

  const stream = new ReadableStream({
    async start(controller) {
      const send = (data: object) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`))
      }
      const entries = readLog()
      entries.forEach(e => send(e))
      lastCount = entries.length

      const interval = setInterval(() => {
        try {
          const current = readLog()
          if (current.length > lastCount) {
            current.slice(lastCount).forEach(e => send(e))
            lastCount = current.length
          }
        } catch {
          clearInterval(interval)
          controller.close()
        }
      }, 3000)

      setTimeout(() => {
        clearInterval(interval)
        controller.close()
      }, 55000)
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    }
  })
}
