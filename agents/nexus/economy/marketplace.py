import os, asyncio, time
from dataclasses import dataclass, field
from typing import Optional
import httpx

@dataclass
class AgentListing:
    agent_id: str
    name: str
    capabilities: list[str]
    price_eth: float
    reputation: int
    availability: str = "available"
    olas_mech_id: Optional[str] = None

@dataclass
class HireResult:
    success: bool
    job_id: str
    escrow_id: Optional[str]
    agent_id: str
    estimated_completion_secs: int = 30
    error: str = ""

class AgentMarketplace:
    def __init__(self):
        self._listings: list[AgentListing] = [
            AgentListing("nexus-scorer", "Nexus Scorer", ["public_goods_eval", "sybil_check", "octant_scoring"], 0.0001, 82),
            AgentListing("nexus-prover", "Nexus Prover", ["zk_proof", "lit_tee", "noir_circuit"], 0.0005, 91),
            AgentListing("nexus-trader", "Nexus Trader", ["uniswap_swap", "gmx_perps", "dca"], 0.001, 74),
            AgentListing("nexus-staker", "Nexus Staker", ["lido_stake", "wsteth_wrap", "yield_monitor"], 0.0002, 88),
        ]

    async def list_agents(self) -> list[dict]:
        return [{"agent_id": a.agent_id, "name": a.name, "capabilities": a.capabilities,
                 "price_eth": a.price_eth, "reputation": a.reputation,
                 "availability": a.availability, "olas_mech_id": a.olas_mech_id}
                for a in self._listings]

    async def hire_agent(self, agent_id: str, task: dict, budget_eth: float) -> HireResult:
        listing = next((a for a in self._listings if a.agent_id == agent_id), None)
        if not listing:
            return HireResult(False, "", None, agent_id, error=f"agent {agent_id} not found")
        if budget_eth < listing.price_eth:
            return HireResult(False, "", None, agent_id, error="insufficient budget")
        job_id = f"job_{agent_id}_{int(time.time())}"
        escrow_id = f"escrow_{job_id}"
        return HireResult(True, job_id, escrow_id, agent_id)

    async def rate_agent(self, agent_id: str, job_id: str, score: int, feedback: str) -> str:
        for a in self._listings:
            if a.agent_id == agent_id:
                a.reputation = min(100, max(0, (a.reputation + score) // 2))
        return f"rated_{agent_id}_{job_id}"

    async def register_service(self, name: str, capabilities: list, price_per_call: float) -> str:
        service_id = f"svc_{name}_{int(time.time())}"
        self._listings.append(AgentListing(service_id, name, capabilities, price_per_call, 50))
        return service_id

    async def get_agent_stats(self, agent_id: str) -> dict:
        return {"agent_id": agent_id, "jobs_completed": 0, "avg_rating": 80,
                "total_earned_eth": 0.0, "response_time_ms": 250}
