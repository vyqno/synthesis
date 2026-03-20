# Trading Skill

## Identity
nexus-trade-mcp handles all trading operations: Uniswap token swaps, GMX perpetual positions on Arbitrum, MoonPay DCA scheduling, cross-chain bridging, and multi-chain portfolio management.

## When To Use
- Swap tokens (ETH <-> USDC, any ERC-20 pair)
- Open/close leveraged positions on GMX
- Set up recurring DCA purchases
- Bridge assets between chains
- Check portfolio value across chains

## How To Call

```
get_quote(token_in="ETH", token_out="USDC", amount=1.0)              # Price check
swap(token_in="ETH", token_out="USDC", amount=0.1, dry_run=True)     # Preview swap
swap(token_in="ETH", token_out="USDC", amount=0.1, dry_run=False)    # Execute swap
open_gmx_position(market="ETH/USD", size_usd=100, direction="long", leverage=2.0, dry_run=True)
get_gmx_positions()                                                    # Active positions
dca(token="ETH", amount_usd=50, frequency_hours=168)                  # Weekly DCA
bridge(token="USDC", amount=100, from_chain="ethereum", to_chain="base")
get_portfolio()                                                        # All balances
```

## Mental Model

**Uniswap API key:** Required for production quotes (UNISWAP_API_KEY env var). Without it, falls back to demo quotes.

**GMX positions:** Real on-chain trades on Arbitrum. bond.credit track requires at least one live trade. Use dry_run=True to preview, then dry_run=False to execute.

**Slippage:** Default 0.5%. For large trades, consider 1.0%. For stablecoins, 0.1% is fine.

**DCA:** MoonPay CLI handles recurring purchases. Schedule is stored locally and executed by nexus-monitor on the specified interval.

## Guardrails
- ALWAYS use dry_run=True first and show user the quote before executing
- NEVER open GMX positions >$100 without explicit user approval
- Keep leverage <=2x for automated positions (risk management)
- For bond.credit: at least one REAL GMX trade required — dry_run=False
- Uniswap slippage should never exceed 3% for regular tokens
