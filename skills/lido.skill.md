# Lido Staking Skill

## Identity
nexus-lido-mcp provides Lido liquid staking operations. It lets any MCP-compatible AI stake ETH, manage stETH/wstETH, monitor vault yields, and participate in Lido governance — without writing any integration code.

## When To Use
- User wants to stake ETH with Lido
- User asks about stETH or wstETH balance
- User wants to monitor Lido vault (EarnETH, EarnUSD) yield
- User wants to participate in Lido DAO governance

## How To Call

```
stake(amount_eth=0.1, dry_run=True)         # Preview staking 0.1 ETH
stake(amount_eth=0.1, dry_run=False)        # Actually stake
get_balance(address="0x...")                # Check stETH/wstETH balances
wrap_steth(amount_steth=1.0, dry_run=True) # Preview wrapping to wstETH
get_vault_yield(vault="earneth")            # Check EarnETH APY vs benchmark
get_governance_proposals()                  # List active votes
vote(proposal_id="...", support=True, dry_run=False)  # Cast vote
```

## Mental Model

**stETH vs wstETH:**
- stETH: rebasing token. Your balance increases every day as rewards accrue. 1 stETH = 1 ETH of stake.
- wstETH: wrapped, non-rebasing. Balance stays fixed; the exchange rate vs stETH grows over time. Better for DeFi protocols that don't handle rebasing.

**Withdrawal Queue:**
- Unstaking takes 1-5 days due to Ethereum's withdrawal queue.
- You get a withdrawal NFT; claim ETH after it's processed.

**EarnETH Vault:**
- Lido's yield-optimized vault: routes stETH to highest-yield DeFi protocols (Aave, Morpho, Pendle, Gearbox, Maple).
- Benchmark: raw stETH staking APY. Vault should beat it.

## Guardrails
- ALWAYS use dry_run=True first to verify expected output
- NEVER stake principal funds without explicit user confirmation
- NEVER call vote() with dry_run=False without confirming proposal details with user
- Withdrawal queue can be 1-5 days — inform user before initiating
