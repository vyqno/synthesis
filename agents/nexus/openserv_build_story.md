# Building Nexus: A Self-Funding Multi-Agent Economy on OpenServ

## The Idea

What if an AI agent didn't need a credit card? What if it earned its own compute budget from DeFi yield, then spent that budget coordinating a team of specialized agents — all through OpenServ?

That's Nexus.

## The Architecture

Nexus holds 1 wstETH in AgentTreasury.sol. Lido's staking protocol generates ~4.2% APY, producing ~0.0042 ETH/day in yield. That yield funds:

1. **Bankr LLM gateway** — multi-model inference (Claude, GPT, Gemini) billed from yield
2. **OpenServ task dispatch** — sub-agents hired for each task, paid per completion
3. **Olas mech requests** — public goods evaluation tasks dispatched to marketplace
4. **Alkahest escrow** — trustless payment released on ZK proof of delivery

## How OpenServ Powers the Coordination Layer

Every task Nexus dispatches goes through `nexus-coordinate-mcp`:

```python
dispatch_task(
    agent_id="nexus-scorer",
    task_description="Evaluate public goods project: github.com/ethereum/ethereum-org-website",
    budget_eth=0.0002
)
```

OpenServ routes this to the registered nexus-scorer agent, tracks completion, and returns the result. Nexus pays only on delivery — no upfront commitment.

## The Self-Funding Loop (Bankr Track)

```
wstETH accrues yield daily
    → agent reads accruedYield() from AgentTreasury.sol
    → withdraws 0.001 ETH to agent wallet
    → swaps to USDC via Uniswap (nexus-trade-mcp)
    → prefunds Bankr LLM gateway
    → all inference billed to Bankr, paid from yield
    → zero human top-ups required
```

agent_log.json records every step. Judges can verify the full loop ran autonomously.

## What We Built in 6 Hours

Using a parallel agent build system (Claude Code dispatching 10+ agents simultaneously):

- Phase 1 (1hr): Repo scaffold + 4 Solidity contracts + Python brain
- Phase 2 (1hr): 4 MCP servers (34 tools) — lido, treasury, identity, trade
- Phase 3 (1hr): 4 more MCP servers (23 tools) + Noir ZK circuits
- Phase 4 (1hr): EigenCompute Docker + Filecoin storage + Octant pipeline
- Phase 5 (1hr): Marketplace layer + cross-chain (Celo, Status, SuperRare)
- Phase 6 (1hr): 9 skill files + manifests + Synthesis API submission

Total: 57 MCP tools, 43 Solidity tests, 3 ZK circuits, 84 committed files.

## The Meta-Point

Nexus demonstrates what agents built on OpenServ can do when they have economic autonomy. Not a demo. A real system.
