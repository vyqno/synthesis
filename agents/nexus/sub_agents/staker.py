"""
nexus-staker — Lido staking manager.

Strategy:
- Polls Lido stETH APY every 15 minutes
- Triggers unstake if APY drops below configurable threshold (default 3%)
- Tracks wstETH position health

Env vars:
    BASE_RPC_URL         — Base mainnet RPC endpoint
    MIN_STAKING_APY      — Minimum acceptable stETH APY (default 3.0)
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from agents.nexus.sub_agents.base import SubAgent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LIDO_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
WSTETH_ADDRESS = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
LIDO_APR_URL = "https://eth-api.lido.fi/v1/protocol/steth/apr/last"


class NexusStaker(SubAgent):
    """
    Autonomous Lido staking manager: monitors APY and triggers rebalance.
    """

    agent_id = "nexus-staker"
    description = "Lido stETH/wstETH staking position manager"

    def __init__(self) -> None:
        super().__init__()
        self.rpc_url: str = os.environ.get("BASE_RPC_URL", "https://mainnet.base.org")
        self.min_apy_threshold: float = float(
            os.environ.get("MIN_STAKING_APY", "3.0")
        )
        self._current_apy: float = 0.0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run_cycle(self) -> dict[str, Any]:
        """
        Decision cycle:
        1. Fetch current stETH APY from Lido API
        2. If APY < threshold: signal unstake (dry-run unless private key set)
        3. Otherwise: hold and log
        """
        result = await self.rebalance_position()
        self.log_action("rebalance_check", result)
        return result

    async def rebalance_position(self) -> dict[str, Any]:
        """Check APY and decide whether to hold or unstake."""
        apy = await self.get_steth_apy()
        self._current_apy = apy

        if apy < self.min_apy_threshold:
            result = {
                "action": "unstake_triggered",
                "apy": apy,
                "threshold": self.min_apy_threshold,
                "dry_run": True,
                "note": "APY below threshold — unstake queued (dry-run)",
            }
        else:
            result = {
                "action": "hold",
                "apy": apy,
                "threshold": self.min_apy_threshold,
            }

        return result

    async def get_steth_apy(self) -> float:
        """Fetch current stETH APR from Lido API. Falls back to 4.0 on error."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(LIDO_APR_URL)
                if r.status_code == 200:
                    return float(r.json().get("data", {}).get("apr", 4.0))
        except Exception:
            pass
        return 4.0

    # ------------------------------------------------------------------
    # Status extension
    # ------------------------------------------------------------------

    async def get_status(self) -> dict[str, Any]:
        base = await super().get_status()
        base["current_apy"] = self._current_apy
        base["min_apy_threshold"] = self.min_apy_threshold
        return base
