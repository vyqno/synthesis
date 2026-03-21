# Nexus System Architecture

Full technical architecture of the Nexus autonomous agent.

---

## Design Principles

- **Yield-funded** — the agent earns its own compute budget from wstETH DeFi yield; no manual top-ups
- **Privacy-first** — all LLM reasoning runs on Venice AI's private-inference nodes; no training data leakage
- **ZK-verified** — disputes, identity claims, and allocation proofs are settled on-chain via Noir ZK circuits
- **Open economy** — any agent can register, earn reputation, and transact via the x402 payment protocol

---

## Chain Assignment

| Component | Chain | Rationale |
|---|---|---|
| AgentTreasury | Base | Low fees, Coinbase infra, x402 native |
| AgentIdentity (ERC-8004) | Multi (canonical) | Same address on 20+ chains |
| NexusArbiter | Base | Barretenberg verifier gas cost is acceptable on Base |
| NexusSliceHook | Base | Uniswap v4 deployed on Base |
| NexusComputeCredit | Base | Primary execution token |
| NexusYieldSplitter | Base | Pendle has Base deployment |
| NexusReputationStaking | Base | Collocated with Arbiter for atomic slash |
| NexusPublicGoodsVault | Base | Octant + Gitcoin both support Base |
| AgentEscrow | Base | Sub-agent payments stay on Base |
| wstETH source | Ethereum mainnet | Lido canonical wstETH |
| Trade execution | Arbitrum | GMX liquidity depth |
| Celo payments | Celo | MiniPay / low-cost micro-payments |

---

## Token Flow

```
ETH (user deposit)
    │
    ▼
Lido stETH
    │   wrap
    ▼
wstETH ──────────────────────────────► AgentTreasury
                                              │
                                    NexusYieldSplitter (Pendle)
                                        │             │
                                       PT          YT yield
                                        │             │
                                  PT holders    NexusComputeCredit
                                               (mint NCC from yield)
                                                      │
                            ┌─────────────────────────┤
                            │                         │
                       burn for                  stake for
                    LLM inference             reputation score
                     (Venice/Groq)          (NexusReputationStaking)
                            │
                    agent operates
                    within budget
```

Surplus yield above the agent's weekly budget is routed to `NexusPublicGoodsVault`:
- 60% → Octant epoch allocation
- 40% → Gitcoin grants round

---

## Agent Decision Loop

1. **Yield harvest** — Keeper sub-agent calls `AgentTreasury.allocateBudget()` every 6 hours; NCC is minted from accrued yield
2. **Budget check** — Brain verifies `NexusComputeCredit.creditBalance()` before calling LLM; queues if budget exhausted
3. **Task intake** — new tasks arrive via Telegram, scheduled cron, MCP tool call, or on-chain event
4. **Private reasoning** — NexusBrain calls Venice AI with the task + agent context; reasoning is private (not stored)
5. **Route** — Brain selects a sub-agent (Trader/Staker/Scorer/Keeper/Prover/Monitor) and passes context
6. **Execute** — sub-agent calls external protocols (Lido, GMX, Uniswap, Olas, Self, Filecoin)
7. **Log** — every action is written to `agent_log.json` and broadcast via SSE to the dashboard
8. **Monitor** — Monitor sub-agent watches for anomalies; sends Telegram alert if threshold breached

---

## ZK Proof Usage

| Circuit | File | When invoked | What it proves |
|---|---|---|---|
| `trade_proof` | `circuits/trade_proof/` | After each closed trade | Execution price matches claimed price in escrow |
| `identity_proof` | `circuits/identity_proof/` | Agent identity challenge | Agent controls ERC-8004 identity without revealing key |
| `allocation_proof` | `circuits/allocation_proof/` | Public goods allocation | Yield split percentages are consistent with treasury state |

All circuits are written in Noir and compiled with `nargo`. Verification keys are deployed to `NexusArbiter`. Proof generation runs in the `prover` sub-agent using Barretenberg WASM.

---

## MCP Server Map

Which sub-agent calls which MCP server:

| Sub-agent | MCP servers used |
|---|---|
| Trader | `nexus-trade-mcp`, `nexus-treasury-mcp` |
| Staker | `nexus-lido-mcp`, `nexus-treasury-mcp` |
| Scorer | `nexus-goods-mcp`, `nexus-coordinate-mcp` |
| Keeper | `nexus-treasury-mcp`, `nexus-lido-mcp` |
| Prover | `nexus-secrets-mcp`, `nexus-identity-mcp` |
| Monitor | `nexus-storage-mcp`, all (read-only log access) |
| Brain (all) | `nexus-identity-mcp` (reputation checks before routing) |

Any MCP-compatible client (Claude, Cursor, GPT-4o) can invoke any of these 57 tools directly via the MCP protocol.

---

## Security Assumptions

**We trust:**
- Lido's wstETH rebasing math (wstETH/stETH ratio is correct)
- Barretenberg's ZK proving system (proof soundness)
- Venice AI's privacy guarantee (no LLM training on agent data)
- Uniswap v4's hook interface (BeforeSwap callback is called correctly)
- Gnosis Safe's multisig security model

**We do not trust:**
- Any single sub-agent's self-reported outcome (all disputes go to ZK arbiter)
- Hot key alone for treasury access (Safe multisig required for principal withdrawal)
- External oracle prices without validation (agent uses on-chain TWAP, not spot)
- The network to deliver proofs atomically (Arbiter has timeout + default-to-client logic)

---

## Known Limitations and Roadmap

### Current Limitations

- **Single brain** — NexusBrain is a single Python process; no redundancy. If it crashes, the agent pauses until restart.
- **Centralized log** — `agent_log.json` is local; not decentralized. Filecoin persistence is async and may lag.
- **ZK proof latency** — Barretenberg WASM proof generation takes 15–90 seconds. Disputes are not instant.
- **x402 SDK unavailable** — The official `x402` Python SDK is targeted for Q2 2026. Manual fallback is used today.
- **ERC-8004 registry** — The canonical address `0x8004A169...` is planned for Jan 2026 launch; pre-launch uses local mock.

### Roadmap

| Quarter | Milestone |
|---|---|
| Q1 2026 | Mainnet deployment on Base; ERC-8004 canonical registry live |
| Q2 2026 | Official x402 Python SDK integration; Pendle yield splitting live |
| Q2 2026 | Multi-brain redundancy (active/standby NexusBrain instances) |
| Q3 2026 | Cross-chain agent discovery via canonical ERC-8004 on 20+ chains |
| Q3 2026 | Decentralized log via Filecoin (replace local JSON) |
| Q4 2026 | DAO governance for NexusPublicGoodsVault allocation parameters |
