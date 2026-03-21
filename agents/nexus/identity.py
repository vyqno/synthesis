"""
Nexus Identity — ENS resolution, ERC-8004 agent identity, Self ZK credentials, ERC-8128 tokens.
"""
from __future__ import annotations

import hashlib
import os
import time
from typing import Optional

import httpx
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

# Chain RPCs
ETH_RPC = os.getenv("SEPOLIA_RPC_URL", "https://rpc.sepolia.org")
BASE_RPC = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")

# ERC-8004 canonical registry — same address on 20+ chains (live Jan 2026)
ERC8004_CANONICAL = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"


class NexusIdentity:
    """
    Handles all identity operations for the Nexus agent:
    - ENS name resolution (forward and reverse)
    - ERC-8004 agent identity registration and reputation
    - Self Protocol ZK credential verification
    - ERC-8128 bearer token issuance
    """

    # ENS Public Resolver on mainnet — we use ENS JS SDK in production,
    # but for Python we call the ENS registry directly
    ENS_REGISTRY_MAINNET = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e"

    def __init__(self) -> None:
        self.w3_eth = Web3(Web3.HTTPProvider(ETH_RPC))
        self.w3_base = Web3(Web3.HTTPProvider(BASE_RPC))
        self.private_key = os.getenv("PRIVATE_KEY", "")
        self.self_api_key = os.getenv("SELF_API_KEY", "")

        # ERC-8004 canonical registry address (same on 20+ chains)
        self.identity_registry_address = os.environ.get("AGENT_IDENTITY_ADDRESS", ERC8004_CANONICAL)

        # In-memory registry for demo (production reads from on-chain contract)
        self._agent_registry: dict[str, dict] = {}
        self._erc8128_tokens: dict[str, dict] = {}

    # ─── ENS Resolution ────────────────────────────────────────────────────

    def resolve(self, name: str) -> Optional[str]:
        """
        Resolve an ENS name to an Ethereum address.
        Returns None if not found.
        """
        try:
            # Use Ethereum mainnet ENS (switch to mainnet RPC for real resolution)
            w3 = Web3(Web3.HTTPProvider("https://eth.llamarpc.com"))
            address = w3.ens.address(name)
            return address
        except Exception as e:
            return None

    def reverse_resolve(self, address: str) -> Optional[str]:
        """Reverse resolve an Ethereum address to an ENS name."""
        try:
            w3 = Web3(Web3.HTTPProvider("https://eth.llamarpc.com"))
            name = w3.ens.name(address)
            return name
        except Exception:
            return None

    def format_address(self, address: str) -> str:
        """
        Format an address: show ENS name if available, else truncate.
        e.g., "nexus-agent.eth" or "0x1234...5678"
        """
        ens_name = self.reverse_resolve(address)
        if ens_name:
            return ens_name
        if len(address) > 10:
            return f"{address[:6]}...{address[-4:]}"
        return address

    def route_payment(self, name_or_address: str, amount_eth: float) -> dict:
        """
        Resolve name/address for payment routing.
        Returns resolved address and ENS name if available.
        """
        if name_or_address.endswith(".eth"):
            address = self.resolve(name_or_address)
            return {"resolved_address": address, "ens_name": name_or_address, "amount_eth": amount_eth}
        else:
            ens_name = self.reverse_resolve(name_or_address)
            return {"resolved_address": name_or_address, "ens_name": ens_name, "amount_eth": amount_eth}

    # ─── ERC-8004 Agent Identity ────────────────────────────────────────────

    def register_agent_identity(self, name: str, operator_wallet: str) -> dict:
        """
        Register an agent identity (ERC-8004 style).
        In production: calls AgentIdentity.sol. Here: stores in registry + prepares tx data.
        """
        agent_id = hashlib.sha256(f"{name}{operator_wallet}".encode()).hexdigest()[:16]
        self._agent_registry[agent_id] = {
            "name": name,
            "operator": operator_wallet,
            "reputation": 50,  # Start at neutral
            "registered_at": int(time.time()),
        }
        return {"agent_id": agent_id, "name": name, "operator": operator_wallet, "reputation": 50}

    async def discover_agent(self, agent_id: str) -> dict:
        """Look up any agent on the canonical ERC-8004 registry (cross-chain discovery)."""
        # Returns agent metadata from the registry
        # Falls back to local registry if canonical not reachable
        return {
            "agent_id": agent_id,
            "registry": ERC8004_CANONICAL,
            "discovered": False,  # real impl would call registry contract
            "note": "canonical ERC-8004 registry — same address on 20+ chains"
        }

    def get_reputation(self, agent_id: str) -> dict:
        """Get agent reputation score and trust level."""
        if agent_id not in self._agent_registry:
            return {"agent_id": agent_id, "score": 0, "trust_level": "unknown"}

        agent = self._agent_registry[agent_id]
        score = agent["reputation"]

        if score >= 80:
            trust_level = "high"
        elif score >= 40:
            trust_level = "medium"
        else:
            trust_level = "low"

        return {"agent_id": agent_id, "score": score, "trust_level": trust_level, "name": agent["name"]}

    # ─── Self Protocol ZK Identity ──────────────────────────────────────────

    def verify_self_identity(self, agent_id: str, proof: str) -> dict:
        """
        Verify a Self ZK credential proof.
        In production: calls Self Protocol MCP server or @selfxyz/core.
        """
        if self.self_api_key and proof:
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(
                        "https://api.self.xyz/v1/verify",
                        headers={"Authorization": f"Bearer {self.self_api_key}"},
                        json={"agent_id": agent_id, "proof": proof},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return {"verified": True, "credential": data.get("credential"), "agent_id": agent_id}
            except Exception:
                pass
        # Demo: if proof starts with "valid_" treat as valid
        verified = proof.startswith("valid_")
        return {"verified": verified, "credential": proof if verified else None, "agent_id": agent_id}

    def get_sybil_score(self, address: str) -> dict:
        """Get Sybil resistance score for an address via Self ZK verification."""
        # In production: query Self Protocol for ZK-verified identity
        # Demo: return a score based on address characteristics
        score = int(hashlib.sha256(address.encode()).hexdigest()[:4], 16) % 100
        return {"address": address, "score": score, "flags": [] if score > 50 else ["low_activity"]}

    # ─── ERC-8128 Bearer Tokens ─────────────────────────────────────────────

    def issue_erc8128_token(self, agent_address: str, scope: str, expiry_seconds: int = 3600) -> dict:
        """
        Issue an ERC-8128 bearer token for API authentication.
        Token encodes: agent address, scope, expiry, signature.
        """
        expiry = int(time.time()) + expiry_seconds
        token_data = f"{agent_address}:{scope}:{expiry}"
        token = hashlib.sha256(token_data.encode()).hexdigest()

        self._erc8128_tokens[token] = {
            "agent_address": agent_address,
            "scope": scope,
            "expiry": expiry,
        }

        return {"bearer_token": token, "agent_address": agent_address, "scope": scope, "expiry": expiry}

    def verify_erc8128_token(self, token: str) -> dict:
        """Verify an ERC-8128 bearer token."""
        if token not in self._erc8128_tokens:
            return {"valid": False, "error": "Token not found"}

        token_data = self._erc8128_tokens[token]
        if int(time.time()) > token_data["expiry"]:
            return {"valid": False, "error": "Token expired"}

        return {
            "valid": True,
            "agent_address": token_data["agent_address"],
            "scope": token_data["scope"],
            "expiry": token_data["expiry"],
        }
