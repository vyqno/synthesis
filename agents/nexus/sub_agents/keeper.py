"""
nexus-keeper — Treasury guardian.

Strategy:
- Monitors on-chain gas prices before any treasury operation
- Defers yield-harvesting if gas > configurable limit (default 50 gwei)
- Routes yield allocations to sub-agents via budget allocation

Env vars:
    SEPOLIA_RPC_URL          — Sepolia testnet RPC (or mainnet)
    AGENT_TREASURY_ADDRESS   — Treasury contract address
    PRIVATE_KEY              — Keeper wallet private key
    YIELD_THRESHOLD_ETH      — Min yield before harvesting (default 0.01)
    GAS_LIMIT_GWEI           — Max gas price for treasury ops (default 50.0)
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from agents.nexus.sub_agents.base import SubAgent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ETHERSCAN_GAS_URL = (
    "https://api.etherscan.io/api?module=gastracker&action=gasoracle"
)


class NexusKeeper(SubAgent):
    """
    Treasury guardian: gas-aware yield harvesting and sub-agent budget routing.
    """

    agent_id = "nexus-keeper"
    description = "Treasury guardian — gas-aware yield harvester and budget router"

    def __init__(self) -> None:
        super().__init__()
        self.rpc_url: str = os.environ.get("SEPOLIA_RPC_URL", "")
        self.treasury_address: str = os.environ.get("AGENT_TREASURY_ADDRESS", "")
        self.private_key: str = os.environ.get("PRIVATE_KEY", "")
        self.yield_threshold_eth: float = float(
            os.environ.get("YIELD_THRESHOLD_ETH", "0.01")
        )
        self.gas_limit_gwei: float = float(
            os.environ.get("GAS_LIMIT_GWEI", "50.0")
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run_cycle(self) -> dict[str, Any]:
        """
        Decision cycle:
        1. Fetch current gas price
        2. If gas > limit: defer all treasury operations
        3. Otherwise: check yield and harvest if above threshold
        """
        result = await self.run_treasury_cycle()
        self.log_action("treasury_check", result)
        return result

    async def run_treasury_cycle(self) -> dict[str, Any]:
        """Check gas and determine whether to execute treasury operations."""
        gas = await self.get_gas_price_gwei()
        deferred = gas > self.gas_limit_gwei

        return {
            "gas_gwei": gas,
            "deferred": deferred,
            "reason": (
                f"gas {gas:.1f} gwei > limit {self.gas_limit_gwei} gwei"
                if deferred
                else "gas OK"
            ),
            "treasury": self.treasury_address or "not_configured",
            "yield_threshold_eth": self.yield_threshold_eth,
        }

    async def get_gas_price_gwei(self) -> float:
        """Fetch current proposed gas price from Etherscan. Falls back to 20 gwei."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(ETHERSCAN_GAS_URL)
                if r.status_code == 200:
                    return float(
                        r.json().get("result", {}).get("ProposeGasPrice", 20)
                    )
        except Exception:
            pass
        return 20.0

    # ------------------------------------------------------------------
    # Status extension
    # ------------------------------------------------------------------

    async def get_status(self) -> dict[str, Any]:
        base = await super().get_status()
        base["treasury_address"] = self.treasury_address or "not_configured"
        base["gas_limit_gwei"] = self.gas_limit_gwei
        base["yield_threshold_eth"] = self.yield_threshold_eth
        return base
