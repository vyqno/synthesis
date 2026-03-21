# Nexus Agent Architecture

The agent layer consists of NexusBrain (LLM orchestrator) and six specialized sub-agents, plus a four-module economy layer.

---

## NexusBrain

`agents/nexus/brain.py`

NexusBrain is the central orchestrator. It receives a task, reasons privately using Venice AI's private-inference LLM, then routes to the appropriate sub-agent.

**LLM provider chain (Bankr → Venice → Groq fallback):**

```
1. Bankr (preferred — on-chain AI payments, native x402)
2. Venice AI (private reasoning — no training on agent data)
3. Groq (fast fallback, llama-3.3-70b)
```

**Core method:** `route_task(task: str) -> str`

- Calls `_think()` with the full task and agent context
- LLM selects which sub-agent to invoke (or handles directly)
- Returns the sub-agent's structured response

---

## Sub-Agents

`agents/nexus/sub_agents/`

| Sub-agent | File | Trigger | Output |
|---|---|---|---|
| `Trader` | `trader.py` | Market opportunity detected, DCA schedule | Swap/position tx via GMX or Uniswap |
| `Staker` | `staker.py` | APY drift, budget surplus | Lido stake/unstake, wstETH rebalance |
| `Scorer` | `scorer.py` | New Octant round, Gitcoin round open | Public goods score, funding allocation |
| `Keeper` | `keeper.py` | Cron: every 6h | Treasury yield harvest, NCC mint |
| `Prover` | `prover.py` | Dispute filed, identity challenge | Noir ZK proof generation + submission |
| `Monitor` | `monitor.py` | Any agent action, anomaly detected | Telegram alert, dashboard SSE push |

Each sub-agent extends `SubAgent` base class and implements `run(context: dict) -> dict`.

---

## Economy Layer

`agents/nexus/economy/`

| Module | File | Purpose |
|---|---|---|
| Marketplace | `marketplace.py` | List/discover agent services with x402 pricing |
| Payments | `payments.py` | Route NCC and ETH payments between agents |
| Reputation | `reputation.py` | Read/update NexusReputationStaking scores |
| Registry | `registry.py` | ERC-8004 agent registration and lookup |

---

## Data Flow

```
Agent action
    │
    ▼
agent_log.json  ←──────── all sub-agent outputs written here
    │
    ▼
Monitor sub-agent
    │
    ├──► Telegram bot (alerts on anomalies)
    │
    └──► Dashboard SSE endpoint  (/api/live-stream)
              │
              ▼
         Browser  (/ · /agents · /economy · /live)
              │
              ▼
         Real-time agent log tiles + portfolio charts
```

---

## Running Locally

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Required environment variables (copy from .env.example)
PRIVATE_KEY=0x...
BASE_RPC_URL=https://mainnet.base.org
SEPOLIA_RPC_URL=https://rpc.sepolia.org
VENICE_API_KEY=...
GROQ_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
AGENT_IDENTITY_ADDRESS=0x8004A169FB4a3325136EB29fA0ceB6D2e539a432

# Start the agent (blocking, runs the main loop)
make agent

# Or run directly
python agents/nexus/main.py
```

---

## Adding a New Sub-Agent

Follow these steps to add a sub-agent to Nexus:

**1. Create the sub-agent file**

```python
# agents/nexus/sub_agents/my_agent.py
from agents.nexus.sub_agents.base import SubAgent

class MyAgent(SubAgent):
    name = "my_agent"
    description = "Does X when Y happens"

    async def run(self, context: dict) -> dict:
        # implement logic
        return {"status": "ok", "result": ...}
```

**2. Add to the ALL_AGENTS registry**

```python
# agents/nexus/sub_agents/__init__.py
from .my_agent import MyAgent

ALL_AGENTS = [Trader, Staker, Scorer, Keeper, Prover, Monitor, MyAgent]
```

**3. Register in main.py**

```python
# agents/nexus/main.py — inside NexusAgent.__init__
self.my_agent = MyAgent(config=self.config)
```

**4. Add routing hint to NexusBrain**

Add a line in `brain.py`'s system prompt describing when to route to `my_agent`.

**5. (Optional) Add an MCP tool**

If other agents or Claude should be able to invoke this sub-agent directly, add a tool in the appropriate MCP server under `mcp/`.

**6. Write tests**

```python
# tests/test_my_agent.py
from agents.nexus.sub_agents.my_agent import MyAgent
```
