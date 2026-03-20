import os, asyncio, time
from dataclasses import dataclass
from typing import Optional
import httpx

@dataclass
class PaymentResult:
    success: bool
    tx_hash: Optional[str]
    amount_eth: float
    timestamp: int = 0
    error: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = int(time.time())

class PaymentEngine:
    def __init__(self):
        self.private_key = os.environ.get("PRIVATE_KEY", "")
        self.base_rpc = os.environ.get("BASE_RPC_URL", "https://mainnet.base.org")
        self._history: list[dict] = []
        self._pending_escrows: list[dict] = []

    async def pay_x402(self, service_url: str, amount_eth: float, description: str) -> PaymentResult:
        headers = {
            "X-Payment": f'{{"type":"x402","amount":"{amount_eth}","token":"ETH","chain":"base"}}',
            "Content-Type": "application/json"
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(service_url, headers=headers, json={"description": description})
                success = r.status_code in (200, 201, 402)
        except Exception:
            success = False
        result = PaymentResult(success, None, amount_eth)
        self._history.append({"type": "x402", "url": service_url, "amount": amount_eth,
                               "description": description, "success": success, "ts": result.timestamp})
        return result

    async def create_escrow(self, recipient: str, amount_eth: float, arbiter: str, description: str) -> str:
        escrow_id = f"escrow_{recipient[:8]}_{int(time.time())}"
        self._pending_escrows.append({
            "escrow_id": escrow_id, "recipient": recipient,
            "amount_eth": amount_eth, "arbiter": arbiter,
            "description": description, "status": "pending", "created_at": int(time.time())
        })
        return escrow_id

    async def release_escrow(self, escrow_id: str, proof: dict) -> bool:
        for e in self._pending_escrows:
            if e["escrow_id"] == escrow_id:
                e["status"] = "released"
                e["proof"] = proof
                return True
        return False

    async def get_pending_payments(self) -> list[dict]:
        return [e for e in self._pending_escrows if e["status"] == "pending"]

    async def get_payment_history(self, limit: int = 20) -> list[dict]:
        return self._history[-limit:]
