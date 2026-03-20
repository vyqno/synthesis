import os, asyncio, time, hashlib
from typing import Optional

class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, dict] = {}
        self.rpc_url = os.environ.get("SEPOLIA_RPC_URL", "")
        self.identity_contract = os.environ.get("AGENT_IDENTITY_ADDRESS", "")

    def _make_id(self, name: str, wallet: str) -> str:
        return "0x" + hashlib.sha256(f"{name}{wallet}".encode()).hexdigest()

    async def register(self, name: str, wallet: str, capabilities: list, price_eth: float) -> str:
        agent_id = self._make_id(name, wallet)
        self._agents[agent_id] = {
            "agent_id": agent_id, "name": name, "wallet": wallet,
            "capabilities": capabilities, "price_eth": price_eth,
            "reputation": 50, "registered_at": int(time.time()), "ens_name": None
        }
        return agent_id

    async def lookup(self, agent_id: str) -> Optional[dict]:
        return self._agents.get(agent_id)

    async def list_all(self) -> list[dict]:
        return list(self._agents.values())

    async def deregister(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False
