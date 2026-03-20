import os, asyncio
from typing import Literal

class InsufficientReputationError(Exception):
    pass

class ReputationGate:
    MIN_REPUTATION_BASIC = 10
    MIN_REPUTATION_TRADE = 50
    MIN_REPUTATION_TREASURY = 80

    TOOL_TIERS = {
        "get_balance": 0, "get_quote": 0, "resolve_ens": 0,
        "swap": 50,
        "open_gmx_position": 50, "dca": 50,
        "withdrawYield": 80, "allocate_budget": 80, "deploy_zyfai_account": 80,
    }

    def __init__(self):
        self._scores: dict[str, int] = {}

    async def _fetch_score(self, agent_id: str) -> int:
        return self._scores.get(agent_id, 50)

    async def check_access(self, agent_id: str, tool_name: str) -> bool:
        score = await self._fetch_score(agent_id)
        required = self.TOOL_TIERS.get(tool_name, 0)
        return score >= required

    async def get_tier(self, agent_id: str) -> Literal["untrusted", "basic", "verified", "trusted"]:
        score = await self._fetch_score(agent_id)
        if score >= 80: return "trusted"
        if score >= 50: return "verified"
        if score >= 10: return "basic"
        return "untrusted"

    async def require_reputation(self, agent_id: str, tool_name: str):
        if not await self.check_access(agent_id, tool_name):
            score = await self._fetch_score(agent_id)
            required = self.TOOL_TIERS.get(tool_name, 0)
            raise InsufficientReputationError(
                f"Agent {agent_id} has score {score}, needs {required} for {tool_name}"
            )

    async def update_reputation(self, agent_id: str, delta: int, reason: str) -> int:
        current = await self._fetch_score(agent_id)
        new_score = min(100, max(0, current + delta))
        self._scores[agent_id] = new_score
        return new_score
