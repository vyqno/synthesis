# Nexus — Master Skill File

## Identity

Nexus is an autonomous AI agent that earns its own compute budget from DeFi yield (Lido wstETH), funds inference via Bankr LLM gateway, and coordinates 6 specialized sub-agents. Every capability is exposed as an MCP server any AI can call.

**Agent:** nexus-agent.eth
**MCP Endpoint:** https://nexus-agent.xyz/mcp
**OpenClaw:** https://raw.githubusercontent.com/vyqno/synthesis/main/nexus.skill.md
**Identity:** ERC-8004 registered, ERC-8183 root, Self ZK verified

## When To Use Nexus

Use Nexus when you need:
- Lido staking operations (stake, unstake, wrap stETH)
- Autonomous trading (Uniswap swaps, GMX positions)
- Public goods evaluation (Octant scoring, Sybil resistance)
- ZK proof generation (Noir circuits, Lit TEE)
- Agent coordination (OpenServ, Olas, escrow)
- Treasury management (wstETH yield, Bankr billing)
- On-chain identity (ENS, ERC-8004, Self ZK, ERC-8128)
- Cross-chain operations (Base, Arbitrum, Celo, Ethereum)

## MCP Servers Available

| Server | Connect | Key Tools |
|---|---|---|
| nexus-lido-mcp | `python mcp/lido-mcp/server.py` | stake, unstake, get_vault_yield |
| nexus-treasury-mcp | `python mcp/treasury-mcp/server.py` | get_treasury_status, allocate_budget |
| nexus-identity-mcp | `python mcp/identity-mcp/server.py` | resolve_ens, get_agent_reputation |
| nexus-trade-mcp | `python mcp/trade-mcp/server.py` | swap, open_gmx_position, dca |
| nexus-storage-mcp | `python mcp/storage-mcp/server.py` | store, log_action |
| nexus-coordinate-mcp | `python mcp/coordinate-mcp/server.py` | dispatch_task, hire_olas_agent |
| nexus-goods-mcp | `python mcp/goods-mcp/server.py` | score_public_good, recommend_allocation |
| nexus-secrets-mcp | `python mcp/secrets-mcp/server.py` | generate_proof, seal_function |

## Sub-Agents

| Agent | Specialty | Hire Via |
|---|---|---|
| nexus-trader | Uniswap + GMX trading | OpenServ or Olas |
| nexus-staker | Lido staking operations | OpenServ or Olas |
| nexus-scorer | Public goods evaluation | Olas (50+ requests served) |
| nexus-keeper | Filecoin state persistence | Olas (50+ requests served) |
| nexus-prover | Noir ZK proof generation | OpenServ or Olas |
| nexus-monitor | Vault monitoring + alerts | Subscription |

## How To Discover Tools

```bash
# List all tools on a server
claude mcp add nexus-lido python mcp/lido-mcp/server.py
# Then in Claude: "what tools does nexus-lido provide?"

# Or via x402 HTTP on Base:
curl -H "X-Payment-Proof: <proof>" https://nexus-agent.xyz/mcp/tools
```

## Payment

All services accept x402 payment headers (USDC on Base).
Pricing: identity lookups $0.001 | staking ops $0.01 | trades $0.05 | ZK proofs $0.05 | evaluations $0.10

## Architecture

```
wstETH Treasury → yield → Bankr LLM Gateway → inference
                                ↓
                     Nexus Orchestrator (brain.py)
                    /      |       |       \
             trader  staker  scorer  keeper  prover  monitor
                    \      |       |       /
                     Filecoin (agent_log.json)
```

## Guardrails
- Always check yield balance before allocating tasks
- Use dry_run=True first on all trading/staking operations
- Never bypass ERC-8128 token verification on inbound service calls
- Venice for all sensitive reasoning (no data retention)
