'use client'
import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts'

interface DataPoint { hour: string; yield_eth: number }
interface Props { data?: DataPoint[]; height?: number }

const MOCK_DATA: DataPoint[] = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  yield_eth: 0.0012 + Math.sin(i / 4) * 0.0003 + Math.random() * 0.0001
}))

export const YieldChart: React.FC<Props> = ({ data = MOCK_DATA, height = 120 }) => (
  <ResponsiveContainer width="100%" height={height}>
    <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
      <defs>
        <linearGradient id="yieldGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
          <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
        </linearGradient>
      </defs>
      <Tooltip
        contentStyle={{ background: '#1e1e2e', border: '1px solid #313244', borderRadius: 6, fontSize: 11 }}
        formatter={(v: number) => [`${v.toFixed(6)} ETH`, 'Yield']}
      />
      <Area type="monotone" dataKey="yield_eth" stroke="#6366f1" fill="url(#yieldGradient)" strokeWidth={2} dot={false} />
    </AreaChart>
  </ResponsiveContainer>
)
