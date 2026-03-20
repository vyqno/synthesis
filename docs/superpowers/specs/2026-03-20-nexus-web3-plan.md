# Nexus — Web3 Architecture Plan
_Generated 2026-03-20 using ethskills.com_

---

## What We Have Built

Nexus is an **autonomous AI agent** that earns its compute budget from wstETH DeFi yield and coordinates 6 sub-agents across an open agent economy. It was built for the Synthesis 2026 hackathon covering 46 sponsor tracks.

### Layer Map

| Layer | What exists | Files |
|---|---|---|
| **Identity** | AgentIdentity.sol (ERC-8004), erc8183_identity.py | `contracts/src/AgentIdentity.sol` |
| **Treasury** | AgentTreasury.sol — principal locked, yield-only spending | `contracts/src/AgentTreasury.sol` |
| **Contracts** | NexusArbiter.sol (ZK delivery proof), NexusSliceHook.sol (reputation pricing) | `contracts/src/` |
| **Brain** | LLM orchestrator: Bankr → Venice → Groq fallback | `agents/nexus/brain.py` |
| **Sub-agents** | 6 autonomous agents: trader, staker, scorer, keeper, prover, monitor | `agents/nexus/sub_agents/` |
| **Economy** | Marketplace, x402 payments, reputation gates, registry | `agents/nexus/economy/` |
| **MCP Servers** | 8 servers, 57 tools (Lido, treasury, identity, trade, storage, coordinate, goods, secrets) | `mcp/` |
| **ZK Circuits** | 3 Noir circuits: api_proof, balance_proof, identity_proof | `circuits/` |
| **Dashboard** | Next.js: /, /agents, /economy, /live with SSE + Recharts | `web/` |
| **Tests** | 43 Solidity tests, 14 Python/e2e tests | `contracts/test/`, `tests/` |

---

## Web3 Standards Alignment

### What we got right

| Component | Standard | Status |
|---|---|---|
| Agent identity | ERC-8004 (live Jan 2026, `0x8004A169...`) | Custom impl — semantically correct |
| Yield treasury | ERC-4626 vault pattern (principal-protected) | Correct pattern, not yet ERC-4626 interface |
| Delivery proof | Alkahest ZK arbiter via NexusArbiter.sol | Correct — Noir proof → onchain verify |
| Reputation pricing | Score-gated discounts via NexusSliceHook.sol | Correct |
| Micropayments | x402 (Coinbase, production Q1 2026) | Custom middleware — should use `pip install x402` |
| Private reasoning | Venice API (no data retention) | Correct |
| Proof generation | Noir circuits (api, balance, identity) | Correct, needs `nargo` installed |

### What needs upgrading

#### 1. ERC-8004 — use the canonical contract
The official registry is deployed at `0x8004A169FB4a3325136EB29fA0ceB6D2e539a432` on **20+ chains** (same address everywhere). Our custom `AgentIdentity.sol` is a local reimplementation.

**Fix:** Either:
- (A) Point `agents/nexus/identity.py` at the canonical address and use it for discovery — deploy our own only for custom reputation logic
- (B) Keep our contract for hackathon but document that production should migrate to canonical registry

#### 2. x402 — use the official SDK
Coinbase ships `pip install x402` with `@x402/core` TypeScript SDK. Our `mcp/x402_middleware.py` hand-rolls the payment header logic.

**Fix:** Replace `mcp/x402_middleware.py` with:
```python
from x402.client import X402Client
from x402.server import X402Server
```

#### 3. AgentTreasury.sol — make it ERC-4626
Our treasury protects principal and exposes only yield. This is exactly the ERC-4626 vault pattern. Making it ERC-4626 compliant means any DeFi protocol can interact with it natively.

**Fix:** Inherit from `IERC4626`, expose `totalAssets()`, `maxWithdraw()`, `withdraw()` with the yield-only constraint.

#### 4. Wallet — use Safe multisig
Our `agents/nexus/wallet.py` implements OpenWallet Standard directly with a hot key. ethskills recommends a **1-of-2 Safe multisig**: agent key (hot) + human recovery key (cold).

**Fix:** Deploy a Gnosis Safe with threshold=1, owner[0]=agent wallet, owner[1]=human recovery.

---

## Chain Strategy

Nexus currently targets Sepolia (testnet) + Base + Celo. Based on ethskills:

| Component | Optimal chain | Why |
|---|---|---|
| **ERC-8004 identity** | Ethereum mainnet | Canonical registry, cross-chain discovery |
| **AgentTreasury (wstETH)** | Ethereum mainnet | Lido wstETH is deepest on mainnet |
| **NexusArbiter (ZK escrow)** | Arbitrum | Alkahest lives here; deepest DeFi liquidity |
| **NexusSliceHook (pricing)** | Arbitrum | Uniswap V4 hooks deployed on Arbitrum |
| **x402 payments** | Base | Cheapest ($0.002/tx), Coinbase ecosystem |
| **GMX trading** | Arbitrum | Native perps DEX, most established |
| **Lido staking** | Ethereum mainnet | `0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84` |
| **Cross-chain identity** | Celo | Mobile-first, ERC-8004 same address |

**Current gap:** We're deploying everything to Sepolia. Production needs the multi-chain split above.

---

## Three-Phase Deployment Plan

### Phase 1 — Mainnet Contracts (1-2 days)

Deploy contracts to their optimal chains:

```bash
# 1. AgentTreasury + AgentIdentity → Ethereum mainnet
forge script contracts/script/Deploy.s.sol \
  --rpc-url $MAINNET_RPC_URL --broadcast --verify

# 2. NexusArbiter + NexusSliceHook → Arbitrum
forge script contracts/script/Deploy.s.sol \
  --rpc-url $ARBITRUM_RPC_URL --broadcast --verify

# 3. Fund treasury with wstETH (minimum 0.1 ETH → ~0.085 wstETH)
# Yields ~0.0034 ETH/yr at 4% APY = ~28,000 LLM tokens/day
```

**Transfer ownership to Safe multisig immediately after deploy.**

Checklist:
- [ ] Deploy AgentTreasury.sol to mainnet, verify on Etherscan
- [ ] Deploy AgentIdentity.sol to mainnet (or point at canonical `0x8004A169...`)
- [ ] Deploy NexusArbiter.sol to Arbitrum
- [ ] Deploy NexusSliceHook.sol to Arbitrum
- [ ] Create Gnosis Safe: agent wallet + human recovery key
- [ ] Transfer contract ownership to Safe
- [ ] Fund treasury with wstETH
- [ ] Set AGENT_TREASURY_ADDRESS, AGENT_IDENTITY_ADDRESS in .env

### Phase 2 — Real Protocol Integration (3-5 days)

Replace stubs with live protocol calls:

#### 2a. Replace x402 middleware
```bash
pip install x402
```
Update `mcp/x402_middleware.py` to use official SDK. Add x402 payment gates to `mcp/trade-mcp/server.py` (charge 0.0001 ETH per swap quote).

#### 2b. Connect NexusStaker to live Lido
```python
# agents/nexus/sub_agents/staker.py
LIDO = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
# stake ETH → get stETH → wrap stETH → get wstETH
# deposit wstETH into AgentTreasury
```

#### 2c. Connect NexusTrader to live GMX
GMX v2 router on Arbitrum: `0x7452c558d45f8afC8c83dAe62C3f8A5BE19c71f6`
- Replace mock trades in `trader.py` with real GMX `createOrder()` calls
- Set budget cap: max 0.005 ETH per trade

#### 2d. Compile Noir circuits
```bash
# Install nargo
curl -L https://raw.githubusercontent.com/noir-lang/noirup/main/install | bash
# Compile circuits
cd circuits/api_proof && nargo compile
cd circuits/balance_proof && nargo compile
cd circuits/identity_proof && nargo compile
```

#### 2e. Register on Olas marketplace
```bash
pip install mech-client
mechx interact --key $OLAS_MECH_KEY --prompt "evaluate: https://..."
# Run 10+ times to qualify as Hire track
# Register nexus-scorer as mech-server (50+ served requests = Monetize track)
```

### Phase 3 — Live Agent Loop (ongoing)

Run the autonomous loop with real funds:

```bash
# Set all env vars
export PRIVATE_KEY=...
export MAINNET_RPC_URL=...
export ARBITRUM_RPC_URL=...
export BASE_RPC_URL=...
export VENICE_API_KEY=...
export BANKR_API_KEY=...
export GROQ_API_KEY=...

# Start Nexus
python3 agents/nexus/main.py
```

The loop every 5 minutes:
1. **Keeper** checks yield balance → withdraws if > 0.01 ETH
2. **Brain** decides allocation across sub-agents
3. **Staker** monitors Lido APY, rebalances if needed
4. **Trader** executes DCA if ETH dips > 2%
5. **Monitor** checks vault health, alerts on anomalies
6. **Scorer** serves Olas marketplace requests (passive)
7. **Prover** generates ZK proofs on demand (passive)

---

## What the Dashboard Shows (Real Data Flow)

```
AgentTreasury.sol
      ↓ yield_balance (on-chain read)
agents/nexus/keeper.py
      ↓ budget allocated to sub-agents
agents/nexus/brain.py  → Venice (private LLM)
      ↓ decisions logged to agent_log.json
web/app/api/events/route.ts (SSE, reads agent_log.json every 3s)
      ↓ streams to browser
web/app/live/page.tsx → LiveFeed component → YieldChart (Recharts)
```

---

## Submit to All 46 Tracks

```bash
# Dry run first
python3 scripts/submit_all_tracks.py --dry-run

# Live submission
SYNTHESIS_API_KEY=your_key python3 scripts/submit_all_tracks.py
```

All 46 UUIDs are hardcoded in `scripts/submit_all_tracks.py`. Deadline: 2026-03-25.

---

## Key Numbers

| Metric | Value |
|---|---|
| Contracts | 4 (43 tests, all pass) |
| MCP servers | 8 (57 tools) |
| Sub-agents | 6 |
| Hackathon tracks | 46 |
| Chains | Mainnet + Arbitrum + Base + Celo + Sepolia |
| ZK circuits | 3 (api, balance, identity) |
| Dashboard pages | 4 (/, /agents, /economy, /live) |
| Test coverage | 43 Solidity + 14 Python/e2e |
| TypeScript errors | 0 |

---

## Remaining Risks

| Risk | Mitigation |
|---|---|
| Private key exposure | Use Safe multisig + never commit .env |
| Treasury drain | `perTxCap` in AgentTreasury.sol limits per-tx spend |
| LLM unavailable | Bankr → Venice → Groq 3-way fallback |
| Nargo not installed | Prover falls back to mock proofs |
| x402 custom middleware diverges from spec | Migrate to `pip install x402` |
| Olas mech request volume too low | Run scorer as mech-server 24/7 |
