# Nexus

> An autonomous agent that earns its own compute budget from DeFi yield and runs an entire economy of specialized sub-agents — without a single human in the loop.

<!-- markee:start -->
<!-- markee:end -->

## What Is Nexus

Nexus is infrastructure for the agentic economy. Any MCP-compatible AI (Claude, Cursor, GPT) can call Nexus capabilities directly from a conversation — staking ETH, evaluating public goods, generating ZK proofs, and coordinating sub-agents.

## MCP Servers

| Server | Purpose | Tools |
|---|---|---|
| `nexus-lido-mcp` | Lido staking + vault monitoring | stake, unstake, wrap_steth, get_vault_yield |
| `nexus-treasury-mcp` | wstETH yield treasury | get_treasury_status, allocate_budget |
| `nexus-identity-mcp` | ERC-8004, ENS, Self ZK | resolve_ens, get_agent_reputation |
| `nexus-trade-mcp` | Uniswap + GMX + MoonPay | swap, open_gmx_position, dca |
| `nexus-storage-mcp` | Filecoin state persistence | store, retrieve, log_action |
| `nexus-coordinate-mcp` | Sub-agent dispatch + escrow | dispatch_agent, hire_olas_agent |
| `nexus-goods-mcp` | Octant public goods scoring | collect_project_data, score_project |
| `nexus-secrets-mcp` | Lit TEE + Noir ZK | seal_function, generate_proof |

## Quick Start

```bash
# Clone and configure
git clone https://github.com/vyqno/synthesis
cd synthesis
cp .env.example .env
# Edit .env with your keys

# Install Python deps
pip install -e ".[dev]"

# Build contracts
cd contracts && forge build

# Run agent
python agents/nexus/main.py
```

## Chains

Ethereum mainnet · Base · Arbitrum · Celo · Status Network Sepolia · Ethereum Sepolia

## Built For

[Synthesis Hackathon 2026](https://synthesis.devfolio.co) — 46 tracks, one project.
