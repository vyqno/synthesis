# Nexus

**Autonomous AI agent powered by DeFi yield**

![Build](https://img.shields.io/badge/build-passing-brightgreen)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue)
![Solidity](https://img.shields.io/badge/Solidity-0.8.25-purple)
![Python](https://img.shields.io/badge/Python-3.12-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

Nexus is an autonomous AI agent that earns its own compute budget from wstETH DeFi yield and operates an entire economy of specialized sub-agents — without a single human in the loop.

---

## Architecture

```
wstETH Yield → AgentTreasury → Keeper → Budget Allocation
                                           ↓
Venice LLM ← NexusBrain (private reasoning) → route_task()
                                           ↓
             ┌──────────┬─────────┬──────────┼──────────┬──────────┐
        Trader      Staker    Scorer    Keeper    Prover   Monitor
             ↓          ↓        ↓         ↓         ↓        ↓
        GMX/Uni   Lido APY  Olas/PGF  Treasury  Noir ZK  Telegram
```

```mermaid
flowchart TD
    Y[wstETH Yield] --> T[AgentTreasury]
    T --> K[Keeper sub-agent]
    K --> B[Budget Allocation]
    B --> Brain[NexusBrain\nVenice LLM / private reasoning]
    Brain --> Trader[Trader\nGMX · Uniswap]
    Brain --> Staker[Staker\nLido APY]
    Brain --> Scorer[Scorer\nOlas · PGF]
    Brain --> Keeper2[Keeper\nTreasury ops]
    Brain --> Prover[Prover\nNoir ZK]
    Brain --> Monitor[Monitor\nTelegram alerts]
    Trader --> Escrow[AgentEscrow]
    Escrow --> Rep[NexusReputationStaking]
    Prover --> Arbiter[NexusArbiter\nZK verification]
    Scorer --> Vault[NexusPublicGoodsVault\nOctant · Gitcoin]
```

---

## Protocol Contracts

| Contract | Chain | Address | Description |
|---|---|---|---|
| `AgentTreasury` | Base | `0x_DEPLOY_` | Holds wstETH principal, releases yield as compute budget |
| `AgentIdentity` | Multi | `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` | ERC-8004 canonical agent identity registry |
| `NexusArbiter` | Base | `0x_DEPLOY_` | Verifies Noir ZK proofs for dispute resolution |
| `NexusSliceHook` | Base | `0x_DEPLOY_` | Uniswap v4 hook — reputation-based swap pricing |
| `NexusComputeCredit` | Base | `0x_DEPLOY_` | ERC-20 credit token; burn for LLM inference |
| `NexusYieldSplitter` | Base | `0x_DEPLOY_` | Splits PT/YT from Pendle; routes yield to agent |
| `NexusReputationStaking` | Base | `0x_DEPLOY_` | Stake NCC; slash on proven fraud |
| `NexusPublicGoodsVault` | Base | `0x_DEPLOY_` | Octant 60% + Gitcoin 40% allocation |
| `AgentEscrow` | Base | `0x_DEPLOY_` | Trustless payment escrow between agents |

---

## MCP Servers

| Server | Purpose | Tools |
|---|---|---|
| `nexus-lido-mcp` | Lido staking + vault monitoring | 8 |
| `nexus-treasury-mcp` | wstETH yield treasury management | 7 |
| `nexus-identity-mcp` | ERC-8004, ENS, Self ZK credentials | 8 |
| `nexus-trade-mcp` | Uniswap + GMX + MoonPay | 9 |
| `nexus-storage-mcp` | Filecoin state persistence | 6 |
| `nexus-coordinate-mcp` | Sub-agent dispatch + escrow | 7 |
| `nexus-goods-mcp` | Octant public goods scoring | 6 |
| `nexus-secrets-mcp` | Lit TEE + Noir ZK proofs | 6 |

**57 tools total** across 8 MCP servers. Any MCP-compatible client (Claude, Cursor, GPT) can call Nexus capabilities directly from a conversation.

---

## Quick Start

```bash
# Clone and configure
git clone https://github.com/vyqno/synthesis
cd synthesis
cp .env.example .env
# Edit .env with your RPC URLs and private key

# Install all dependencies
make install

# Start the full stack (agent + dashboard)
make dev
```

---

## Deployment

```bash
# Deploy to Sepolia (testnet)
make deploy-sepolia

# Deploy to production (mainnet + Base + Arbitrum + Celo)
make deploy-mainnet
```

After deployment, set contract addresses in `.env` and restart the agent.

---

## Track Coverage

Covers **46 sponsor tracks** across [Synthesis 2026](https://synthesis.devfolio.co):

- Lido (wstETH yield source, staking sub-agent)
- Uniswap v4 (NexusSliceHook, swap routing)
- Coinbase / Base (primary execution chain, x402 payments, AgentKit)
- Venice AI (private LLM reasoning — brain.py)
- Noir (3 ZK circuits: trade proof, identity proof, allocation proof)
- Filecoin (agent state persistence via storage-mcp)
- Olas (public goods scoring, agent coordination)
- Self Protocol (ZK identity verification)
- ENS (name resolution for payment routing)
- Gnosis Safe (multisig key management)
- Octant + Gitcoin (public goods fund allocation)
- GMX (leveraged trading sub-agent)
- Lit Protocol (TEE secret management)
- Pendle (yield splitting PT/YT)
- MoonPay (fiat on-ramp integration)
- _...and 31 more_

---

## Tech Stack

| Layer | Technology |
|---|---|
| Smart contracts | Solidity 0.8.25, Foundry |
| Agent runtime | Python 3.12, asyncio |
| LLM | Venice AI (private) → Groq → Bankr fallback |
| ZK proofs | Noir + Barretenberg |
| Dashboard | Next.js 15, TypeScript, Tailwind |
| MCP servers | FastMCP (Python) |
| Chains | Ethereum · Base · Arbitrum · Celo |
| Identity | ERC-8004 canonical registry |
| Payments | x402 protocol (Coinbase) |
| Storage | Filecoin / IPFS |

---

---

## Student Founder's Bet — College.xyz Track

> **Track:** [Student Founder's Bet](https://www.college.xyz/bounties/26) × Synthesis 2026
> **Sponsor:** College.xyz
> **Prize:** $2,500

### Builder

**Hitesh P**
BMS College of Engineering, Bengaluru
B.Sc. (Business Systems) — Class of 2028
Email: hiteshp.bs24@bmsce.ac.in
Telegram: [@vyqno](https://t.me/vyqno)

### Student Proof

Active enrollment — Semester 4, all courses Registered:

![Student Enrollment Proof](docs/student-proof.png)

*BMS College of Engineering — course registration showing active enrollment (ID redacted per track rules)*

### Why Nexus qualifies

Nexus started as a genuine attempt to solve a real problem: **AI agents can't pay for themselves**. Every LLM call costs money, and every autonomous agent needs a human to top up a credit card. That's not autonomy — it's dependency.

The solution: lock wstETH principal in a smart contract, let the agent spend only yield. The agent earns its own compute budget through DeFi, reasons privately through Venice, and coordinates a swarm of sub-agents through an open economy — all without touching the depositor's principal.

This isn't a hackathon demo. It's a protocol:
- 9 contracts (4 battle-tested + 5 novel DeFi primitives)
- 142 tests passing (86 Foundry + 56 Python)
- 8 MCP servers, 57 tools, 6 sub-agents
- Real yield-splitting, real ZK proofs, real agent escrow
- Covers 46 sponsor tracks across Synthesis 2026

Built solo, in one week, at 3am between classes.

---

## License

MIT. See [LICENSE](LICENSE).

## Contributing

PRs welcome. Run `make test` before submitting. See `docs/architecture.md` for system design.
