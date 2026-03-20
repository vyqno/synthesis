"""
SubAgent base class — shared interface for all Nexus sub-agents.

Each sub-agent:
- Has a unique agent_id and budget allocation from treasury yield
- Runs its own async decision cycle
- Logs all actions to agent_log.json via brain.py log_action
- Reports status via get_status()
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Literal

from agents.nexus.brain import log_action


class SubAgent(ABC):
    """
    Abstract base class for all Nexus sub-agents.

    Subclasses must implement run_cycle() with their specific decision logic.
    """

    agent_id: str
    description: str = ""

    def __init__(self) -> None:
        self.budget_eth: float = 0.0
        self.status: Literal["idle", "running", "paused", "error"] = "idle"
        self.last_action: dict[str, Any] = {}
        self.action_log: list[dict[str, Any]] = []
        self._started_at: float = time.monotonic()
        self._cycle_count: int = 0
        self._error_count: int = 0

    # ------------------------------------------------------------------
    # Abstract interface — subclasses must implement
    # ------------------------------------------------------------------

    @abstractmethod
    async def run_cycle(self) -> dict[str, Any]:
        """
        Execute one decision cycle.

        Returns a dict describing the action taken, e.g.:
            {"action": "buy_eth", "amount": 0.01, "tx_hash": "0x..."}
        """

    # ------------------------------------------------------------------
    # Concrete helpers available to all sub-agents
    # ------------------------------------------------------------------

    def allocate_budget(self, eth: float) -> None:
        """Add ETH to this agent's budget (called by keeper)."""
        self.budget_eth += eth
        log_action(
            f"{self.agent_id}.budget_allocated",
            {"added_eth": eth, "total_budget_eth": self.budget_eth},
        )

    def deduct_budget(self, eth: float, reason: str = "") -> bool:
        """
        Deduct ETH from budget. Returns False if insufficient funds.
        Enforces 20% per-trade cap implicitly via caller checks.
        """
        if eth > self.budget_eth:
            log_action(
                f"{self.agent_id}.budget_insufficient",
                {"requested_eth": eth, "available_eth": self.budget_eth, "reason": reason},
            )
            return False
        self.budget_eth -= eth
        log_action(
            f"{self.agent_id}.budget_spent",
            {"spent_eth": eth, "remaining_eth": self.budget_eth, "reason": reason},
        )
        return True

    def log_action(self, action: str, result: dict[str, Any]) -> None:
        """Append an action to the in-memory log and agent_log.json."""
        entry: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent_id": self.agent_id,
            "action": action,
            "result": result,
        }
        self.action_log.append(entry)
        self.last_action = entry
        log_action(f"{self.agent_id}.{action}", result)

    def set_status(self, status: Literal["idle", "running", "paused", "error"]) -> None:
        """Update agent status."""
        self.status = status

    async def get_status(self) -> dict[str, Any]:
        """Return a standardised status snapshot."""
        uptime_s = time.monotonic() - self._started_at
        return {
            "agent_id": self.agent_id,
            "description": self.description,
            "status": self.status,
            "budget_eth": self.budget_eth,
            "last_action": self.last_action,
            "uptime_seconds": round(uptime_s, 1),
            "cycle_count": self._cycle_count,
            "error_count": self._error_count,
        }

    async def _safe_run_cycle(self) -> dict[str, Any]:
        """Wraps run_cycle() with status tracking and error handling."""
        self.set_status("running")
        self._cycle_count += 1
        try:
            result = await self.run_cycle()
            self.set_status("idle")
            return result
        except Exception as exc:
            self._error_count += 1
            self.set_status("error")
            self.log_action("cycle_error", {"error": str(exc), "cycle": self._cycle_count})
            return {"action": "error", "error": str(exc)}
