<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=NEXUS&fontSize=80&fontColor=fff&animation=twinkling&fontAlignY=35&desc=The%20protocol%20that%20funds%20itself&descAlignY=55&descSize=18" width="100%" />

<br/>

[![Live](https://img.shields.io/badge/STATUS-LIVE-22C55E?style=for-the-badge&logo=ethereum&logoColor=white&labelColor=09090B)](.)
[![Python](https://img.shields.io/badge/Python-3.12-A855F7?style=for-the-badge&logo=python&logoColor=white&labelColor=09090B)](.)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.25-EC4899?style=for-the-badge&logo=solidity&logoColor=white&labelColor=09090B)](./contracts)
[![Tests](https://img.shields.io/badge/Tests-182%20passing-F59E0B?style=for-the-badge&logo=pytest&logoColor=white&labelColor=09090B)](.)
[![License](https://img.shields.io/badge/License-MIT-38BDF8?style=for-the-badge&logoColor=white&labelColor=09090B)](./LICENSE)

<br/>

```
╔══════════════════════════════════════════════════════════════════╗
║  wstETH earns yield  →  yield pays for compute  →  repeat ∞     ║
╚══════════════════════════════════════════════════════════════════╝
```

**Nexus stakes ETH, earns 4.2% APY, and uses that yield to fund its own operations — forever.**
No human top-ups. No subscription. No limits.

<br/>

[**→ Dashboard**](http://localhost:3000/dashboard) · [**→ Operators**](http://localhost:3000/agents) · [**→ Market**](http://localhost:3000/economy) · [**→ Activity**](http://localhost:3000/live)

</div>

---

## What is Nexus?

Nexus is an **autonomous AI agent protocol** built on Ethereum. It solves the hardest problem in AI agent design: *agents need money to operate, and giving them open access to money is dangerous.*

**The Nexus solution:** deposit ETH once, stake it via Lido for wstETH, and let the **yield** — not the principal — pay for everything. The principal is always safe. The agent runs forever.

> *"The first AI agent with a genuinely self-sustaining economic model."*

---

## Why This is a Great Project

Most AI agent projects fail in production for one simple reason: **they run out of money.**

| Approach | Problem |
|----------|---------|
| Pre-funded wallets | Limited lifespan, single point of failure |
| Human top-ups | Requires constant monitoring, defeats autonomy |
| Subscription models | Doesn't scale, external dependency |
| **Nexus yield model** | ✅ Infinite lifespan, principal protected, scales with TVL |

**What makes Nexus technically exceptional:**

- 🔁 **Self-funding loop** — yield → compute → action → reputation → more yield
- 🔒 **Principal safety** — 1 ETH deposited is always 1 ETH redeemable (wstETH ERC-4626)
- 🧠 **Private reasoning** — Venice AI for on-device LLM inference, no data leakage
- ⚡ **ZK identity** — ERC-8004 canonical agent registry, Noir proof generation
- 🏦 **Agent economy** — hire/fire agents via `AgentEscrow`, slash bad actors via `NexusReputationStaking`
- 📦 **8 MCP servers** — 57 tools any Claude agent can call immediately
- 🧪 **182 tests** — 86 Foundry (unit + fuzz + invariant) + 96 Python (integration + e2e)
- 🌐 **Multi-chain** — Mainnet (staking), Arbitrum (perps), Base (payments), Celo (mobile)

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│   You deposit 1 ETH                                              │
│          ↓                                                        │
│   Lido stakes it → 0.942 wstETH (4.2% APY)                      │
│          ↓                                                        │
│   Each epoch: ~0.0042 ETH yield harvested by Keeper agent        │
│          ↓                                                        │
│   Keeper allocates yield budget to 6 operator agents             │
│          ↓                                                        │
│   Agents execute: trade · stake · score · prove · monitor        │
│          ↓                                                        │
│   Earn reputation + USDC → re-stake → repeat ∞                   │
│                                                                   │
│   Your 1 ETH principal: untouched. Always redeemable.            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture

```mermaid
graph TB
    subgraph "Economic Engine"
        D[ETH Deposit] --> L[Lido Staking]
        L --> W[wstETH 4.2% APY]
        W --> T[AgentTreasury ERC-4626]
    end

    subgraph "Intelligence Core"
        T --> K[Keeper]
        K --> V[Venice AI Private LLM]
        V --> R[NexusBrain Router]
    end

    subgraph "Operator Swarm"
        R --> TR[Trader · GMX · Uniswap]
        R --> ST[Staker · Lido · EigenLayer]
        R --> SC[Scorer · Olas · Impact]
        R --> PR[Prover · Noir · Lit TEE]
        R --> MO[Monitor · Chainlink]
    end

    subgraph "Protocol Contracts"
        TR --> AE[AgentEscrow]
        SC --> PG[PublicGoodsVault]
        PR --> RS[ReputationStaking]
        AE --> ARB[NexusArbiter]
    end

    subgraph "Identity"
        R --> ID[ERC-8004 · 0x8004A1...9432]
    end
```

---

## Agent Swarm

| Operator | Role | Protocols | Networks |
|----------|------|-----------|---------|
| **Trader** | DCA execution, perpetuals | GMX, Uniswap v4 | Arbitrum, Base |
| **Staker** | Yield optimization | Lido, EigenLayer | Mainnet |
| **Scorer** | Impact evaluation, anti-sybil | Olas, Venice AI | Mainnet |
| **Prover** | ZK identity & computation proofs | Noir, Lit Protocol | Base |
| **Keeper** | Treasury guardian, gas optimization | ERC-4626, Chainlink | Mainnet |
| **Monitor** | Protocol health, alert system | Chainlink, Telegram | All |

**Real session stats:** `105 logged actions · 48 on-chain txs · 14 ZK proofs · 24.36 USDC earned`

---

## Protocol Contracts

| Contract | Purpose | Key Feature |
|----------|---------|-------------|
| `AgentTreasury` | ERC-4626 yield vault | Self-funding compute budget |
| `NexusComputeCredit` | ETH-backed ERC-20 | `burnForService()`, 0.1% fee |
| `NexusYieldSplitter` | Pendle-style PT/YT | Donate yield, keep principal |
| `NexusReputationStaking` | EigenLayer-style staking | 3-of-N slash, 7d cooldown |
| `NexusPublicGoodsVault` | Soulbound yield donor | 60% Octant / 40% Gitcoin |
| `AgentEscrow` | ZK-verified labor market | 2% insurance, 10% late penalty |
| `AgentIdentity` | ERC-8004 registry | 20+ chains, canonical |
| `NexusArbiter` | Dispute resolution | On-chain arbitration |

---

## Deployed Contracts (Ethereum Sepolia — 2026-03-21)

**Network:** Sepolia testnet (chain ID 11155111)
**Deployer:** `0x814a3D96C36C45e92159Ce119a82b3250Aa79E5b`

| Contract | Address | Sepolia Explorer |
|----------|---------|-----------------|
| `AgentTreasury` | `0xc54c77991B8fac16aB9856d8d33d563701925aFE` | [View](https://sepolia.etherscan.io/address/0xc54c77991B8fac16aB9856d8d33d563701925aFE) |
| `AgentIdentity` | `0xd81e007F671F87659D2A9Ff0C51Ea83B61F13BAD` | [View](https://sepolia.etherscan.io/address/0xd81e007F671F87659D2A9Ff0C51Ea83B61F13BAD) |
| `NexusArbiter` | `0x617BD18d26844069dE0a6b8A9c60F9F1b079E11F` | [View](https://sepolia.etherscan.io/address/0x617BD18d26844069dE0a6b8A9c60F9F1b079E11F) |
| `NexusComputeCredit` | `0x640690E6159161b15466D38CCA63174dC66C6214` | [View](https://sepolia.etherscan.io/address/0x640690E6159161b15466D38CCA63174dC66C6214) |
| `NexusReputationStaking` | `0xA09F93423FD2E6065402C111605e89F3E2645492` | [View](https://sepolia.etherscan.io/address/0xA09F93423FD2E6065402C111605e89F3E2645492) |
| `NexusYieldSplitter` | `0x106226Ea0B12aDF164633b30b3fdec3f3Db0feD7` | [View](https://sepolia.etherscan.io/address/0x106226Ea0B12aDF164633b30b3fdec3f3Db0feD7) |
| `NexusPublicGoodsVault` | `0x9601fc397bD36005C2d7dD76Ec5C2C8810871a2A` | [View](https://sepolia.etherscan.io/address/0x9601fc397bD36005C2d7dD76Ec5C2C8810871a2A) |
| `AgentEscrow` | `0xE744c11C144AD9158368Fbe62c35DA13ac44A2d7` | [View](https://sepolia.etherscan.io/address/0xE744c11C144AD9158368Fbe62c35DA13ac44A2d7) |
| `NexusSliceHook` | `0xF2Dc77a7008e2EcbB1eB067f8d929F287F8DAAbF` | [View](https://sepolia.etherscan.io/address/0xF2Dc77a7008e2EcbB1eB067f8d929F287F8DAAbF) |
| `AgentPay` | `0x9A2add8AFa7f50F4a2343F628E36ec00485C7362` | [View](https://sepolia.etherscan.io/address/0x9A2add8AFa7f50F4a2343F628E36ec00485C7362) |
| `AgentTrust` | `0xdcAe729E23Ad735614EccbDC022261cBB4A444A6` | [View](https://sepolia.etherscan.io/address/0xdcAe729E23Ad735614EccbDC022261cBB4A444A6) |
| `AgentCooperate` | `0x1d75e4C99AF6B75EC8F876eAAa4f7489e34EF707` | [View](https://sepolia.etherscan.io/address/0x1d75e4C99AF6B75EC8F876eAAa4f7489e34EF707) |
| `AgentSecrets` | `0x9f9675affd48c0402F8f277E0376D70FB3a7D1ca` | [View](https://sepolia.etherscan.io/address/0x9f9675affd48c0402F8f277E0376D70FB3a7D1ca) |
| `AlkahestZKArbiter` | `0xf6f1F7B48b158d627Fd6313DC1C6aaf45f90a23B` | [View](https://sepolia.etherscan.io/address/0xf6f1F7B48b158d627Fd6313DC1C6aaf45f90a23B) |

---

## MCP Servers (57 Tools)

```
nexus-lido-mcp       stake, unstake, get_apy, harvest_yield, get_balance
nexus-treasury-mcp   vault_state, yield_tracker, budget_allocate, withdraw
nexus-identity-mcp   register, verify, discover, list_agents, get_proof
nexus-trade-mcp      quote, swap, open_position, close_position, get_price
nexus-storage-mcp    store, retrieve, pin_ipfs, get_cid, delete
nexus-coordinate-mcp hire_agent, release_agent, create_escrow, resolve
nexus-goods-mcp      score_project, fund_public_good, get_impact_score
nexus-secrets-mcp    generate_proof, verify_proof, encrypt, decrypt
```

---

## Stack

| Layer | Tech |
|-------|------|
| **Contracts** | Solidity 0.8.25 · Foundry · OpenZeppelin · ERC-4626 · ERC-8004 |
| **Agent** | Python 3.12 · asyncio · Venice AI · Groq · Olas Mech |
| **ZK** | Noir · Barretenberg · Lit Protocol TEE |
| **Payments** | x402 HTTP payment protocol · Gnosis Safe 1-of-2 |
| **Dashboard** | Next.js 14 · Framer Motion · Tailwind CSS |
| **DeFi** | Lido · Uniswap v4 · GMX · Pendle · EigenLayer |
| **Infra** | Docker · GitHub Actions · EigenCompute · IPFS |

---

## Quickstart

```bash
git clone https://github.com/vyqno/nexus-protocol
cd nexus-protocol/synthesis

# Python agent
pip install -r requirements.txt
cp .env.example .env  # fill in keys
python3 agents/nexus/main.py

# Dashboard
cd web && npm install && npm run dev
# → http://localhost:3000

# Contracts
cd contracts && forge test -vv
make deploy-sepolia
```

---

<div align="center">

**Built by [Hitesh P](https://github.com/vyqno) · BMSCE Bangalore · 2026**

```
"Give an agent a budget and it runs for a day.
 Give it yield and it runs forever."
```

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer&animation=twinkling" width="100%" />

</div>
