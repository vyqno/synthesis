# Treasury Management Skill

## Identity
nexus-treasury-mcp manages the Nexus wstETH treasury. It tracks yield accrual, allocates compute budgets to sub-agents, integrates Zyfai for idle yield optimization, and closes the loop by funding Bankr LLM inference directly from wstETH yield.

## When To Use
- Check available compute budget before dispatching a sub-agent
- Allocate yield budget to a sub-agent task
- Log inference spend for treasury accounting
- Deploy idle USDC to Zyfai yield accounts

## How To Call

```
get_treasury_status()                              # Full treasury overview
allocate_budget(agent_id="nexus-trader", amount_eth=0.001)  # Assign budget
get_agent_budget(agent_id="nexus-scorer")          # Check remaining budget
log_inference_spend(agent_id="nexus-trader", model="claude-3-5-haiku", tokens=1000, cost_usd=0.001)
simulate_yield_funding_loop()                      # Demo Bankr yield→inference loop
```

## Mental Model

**Principal protection:** The agent NEVER touches the 1 ETH principal. Only yield (accrued via wstETH rebasing) flows to compute budgets.

**Yield→inference loop:**
1. wstETH balance grows daily (staking rewards)
2. Agent reads `accruedYield()` from AgentTreasury.sol
3. Withdraws yield to agent wallet (subject to perTxCap)
4. Swaps ETH → USDC via Uniswap
5. Prefunds Bankr LLM gateway
6. All sub-agent inference is billed to Bankr — paid from yield

**Zyfai:** Idle USDC sits in Zyfai accounts earning additional yield while waiting to be spent on inference.

## Guardrails
- NEVER withdraw principal (only accrued yield)
- ALWAYS check `get_agent_budget()` before dispatching expensive operations
- Log every inference spend with `log_inference_spend()` — judges verify agent_log.json
