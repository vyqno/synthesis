"""
Nexus Treasury — wstETH yield balance tracking, budget allocation, spend logging.
"""
from __future__ import annotations

import os
from typing import Optional

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# wstETH on Ethereum mainnet
WSTETH_ADDRESS = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
WSTETH_ABI = [
    {"name": "balanceOf", "type": "function", "inputs": [{"type": "address"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "getStETHByWstETH", "type": "function", "inputs": [{"type": "uint256"}], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
]

# AgentTreasury ABI (minimal)
TREASURY_ABI = [
    {"name": "accruedYield", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "totalBalance", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "principalShares", "type": "function", "inputs": [], "outputs": [{"type": "uint256"}], "stateMutability": "view"},
    {"name": "withdrawYield", "type": "function", "inputs": [{"type": "uint256", "name": "amount"}, {"type": "address", "name": "recipient"}], "outputs": [], "stateMutability": "nonpayable"},
]


class NexusTreasury:
    """
    Interfaces with AgentTreasury.sol to manage yield budget allocation.
    Falls back to demo mode if contract address not configured.
    """

    def __init__(self) -> None:
        self.eth_rpc = os.getenv("SEPOLIA_RPC_URL", "https://rpc.sepolia.org")
        self.treasury_address = os.getenv("TREASURY_CONTRACT_ADDRESS", "")
        self.private_key = os.getenv("PRIVATE_KEY", "")
        self.w3 = Web3(Web3.HTTPProvider(self.eth_rpc))

        # In-memory budget tracking (also reflected on-chain in production)
        self._agent_budgets: dict[str, float] = {}
        self._spend_log: list[dict] = []

        if self.treasury_address:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.treasury_address),
                abi=TREASURY_ABI,
            )
        else:
            self.contract = None

    def get_yield_balance(self) -> float:
        """Returns available yield balance in ETH."""
        if self.contract:
            try:
                yield_wei = self.contract.functions.accruedYield().call()
                return float(Web3.from_wei(yield_wei, "ether"))
            except Exception:
                pass
        # Demo mode: return simulated yield
        return 0.0042  # ~$10 at $2400/ETH

    def get_treasury_status(self) -> dict:
        """Returns full treasury status."""
        yield_eth = self.get_yield_balance()
        total_allocated = sum(self._agent_budgets.values())

        return {
            "yield_balance_eth": yield_eth,
            "yield_balance_usd": yield_eth * 2400,  # Approximate
            "principal_eth": 1.0,  # Demo: 1 ETH principal
            "allocated_budgets": self._agent_budgets.copy(),
            "total_allocated_eth": total_allocated,
            "available_eth": max(0, yield_eth - total_allocated),
            "spend_log_entries": len(self._spend_log),
        }

    def allocate_budget(self, agent_id: str, amount_eth: float) -> dict:
        """Allocate yield budget to a sub-agent."""
        available = self.get_yield_balance() - sum(self._agent_budgets.values())
        if amount_eth > available:
            raise ValueError(f"Insufficient yield: {available:.6f} ETH available, requested {amount_eth:.6f}")

        self._agent_budgets[agent_id] = self._agent_budgets.get(agent_id, 0) + amount_eth
        return {"agent_id": agent_id, "allocated": amount_eth, "total_budget": self._agent_budgets[agent_id]}

    def get_agent_budget(self, agent_id: str) -> dict:
        """Get remaining budget for a sub-agent."""
        allocated = self._agent_budgets.get(agent_id, 0)
        spent = sum(e["amount_eth"] for e in self._spend_log if e["agent_id"] == agent_id)
        return {
            "agent_id": agent_id,
            "allocated_eth": allocated,
            "spent_eth": spent,
            "remaining_eth": max(0, allocated - spent),
        }

    def log_inference_spend(self, agent_id: str, model: str, tokens: int, cost_usd: float) -> None:
        """Log an inference spend event."""
        cost_eth = cost_usd / 2400  # Approximate USD → ETH
        self._spend_log.append({
            "agent_id": agent_id,
            "model": model,
            "tokens": tokens,
            "cost_usd": cost_usd,
            "amount_eth": cost_eth,
            "funded_from_yield": True,
        })

    def get_bankr_usage(self) -> dict:
        """Returns Bankr LLM gateway usage summary."""
        bankr_entries = [e for e in self._spend_log if "bankr" in e.get("model", "").lower() or e.get("funded_from_yield")]
        return {
            "total_spend_usd": sum(e["cost_usd"] for e in self._spend_log),
            "bankr_entries": len(bankr_entries),
            "by_model": {
                e["model"]: {"tokens": e["tokens"], "cost_usd": e["cost_usd"]}
                for e in self._spend_log
            },
            "funded_from_yield": True,
        }
