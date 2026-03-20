"""
Nexus Wallet — OpenWallet Standard (OWS) implementation.
OWS is MoonPay's CC0 open-source wallet standard for local-first, chain-agnostic wallet management.
Track: OpenWallet Standard ($3.5k)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from eth_account import Account
from dotenv import load_dotenv

load_dotenv()

WALLET_STATE_FILE = Path(__file__).parent.parent.parent / "wallet_state.json"


@dataclass
class ChainPlugin:
    """OWS chain plugin — encapsulates chain-specific logic."""
    chain_id: int
    name: str
    rpc_url: str
    native_token: str
    usdc_address: str


@dataclass
class SpendingPolicy:
    """OWS spending policy — controls what the agent can spend."""
    policy_type: str  # "yield-only", "whitelist", "per-tx-cap"
    per_tx_cap_eth: float = 0.01
    whitelist: list = field(default_factory=list)
    yield_only: bool = True  # Agent can only spend yield, not principal


@dataclass
class NexusWallet:
    """
    OpenWallet Standard wallet for Nexus.
    Manages keys and policy across Base, Ethereum, Arbitrum, Celo.
    """
    address: str
    chains: dict[str, ChainPlugin] = field(default_factory=dict)
    policies: dict[str, SpendingPolicy] = field(default_factory=dict)


# Chain registry (OWS chain plugins)
CHAIN_PLUGINS = {
    "ethereum": ChainPlugin(
        chain_id=1,
        name="Ethereum Mainnet",
        rpc_url=os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com"),
        native_token="ETH",
        usdc_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    ),
    "base": ChainPlugin(
        chain_id=8453,
        name="Base Mainnet",
        rpc_url=os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
        native_token="ETH",
        usdc_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    ),
    "arbitrum": ChainPlugin(
        chain_id=42161,
        name="Arbitrum One",
        rpc_url=os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
        native_token="ETH",
        usdc_address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    ),
    "celo": ChainPlugin(
        chain_id=42220,
        name="Celo Mainnet",
        rpc_url=os.getenv("CELO_RPC_URL", "https://forno.celo.org"),
        native_token="CELO",
        usdc_address="0xcebA9300f2b948710d2653dD7B07f33A8B32118C",
    ),
}

# Default spending policy for Nexus: yield-only, $10 per-tx cap
DEFAULT_POLICY = SpendingPolicy(
    policy_type="yield-only",
    per_tx_cap_eth=0.01,
    whitelist=["bankr", "zyfai", "openserv", "lido"],
    yield_only=True,
)


def load_wallet() -> NexusWallet:
    """Load wallet state from disk or create new."""
    pk = os.getenv("PRIVATE_KEY", "")
    if pk:
        address = Account.from_key(pk).address
    else:
        address = "0x0000000000000000000000000000000000000000"

    if WALLET_STATE_FILE.exists():
        state = json.loads(WALLET_STATE_FILE.read_text())
        return NexusWallet(address=state.get("address", address), chains=CHAIN_PLUGINS)

    wallet = NexusWallet(address=address, chains=CHAIN_PLUGINS)
    wallet.policies["default"] = DEFAULT_POLICY
    _save_wallet(wallet)
    return wallet


def _save_wallet(wallet: NexusWallet) -> None:
    state = {
        "address": wallet.address,
        "chains": [c for c in wallet.chains.keys()],
        "policy": asdict(DEFAULT_POLICY),
    }
    WALLET_STATE_FILE.write_text(json.dumps(state, indent=2))


def check_policy(action: str, amount_eth: float, recipient: str = "") -> dict:
    """
    OWS policy check — verify an action is permitted before executing.
    Returns: {allowed: bool, reason: str}
    """
    if amount_eth > DEFAULT_POLICY.per_tx_cap_eth:
        return {"allowed": False, "reason": f"Exceeds per-tx cap: {amount_eth} ETH > {DEFAULT_POLICY.per_tx_cap_eth} ETH"}

    if DEFAULT_POLICY.whitelist and recipient:
        in_whitelist = any(w in recipient.lower() for w in DEFAULT_POLICY.whitelist)
        if not in_whitelist and amount_eth > 0.001:
            return {"allowed": False, "reason": f"Recipient not in whitelist: {recipient}"}

    return {"allowed": True, "reason": "Policy check passed"}


def get_wallet_status() -> dict:
    """Return current wallet status across all chains."""
    wallet = load_wallet()
    return {
        "address": wallet.address,
        "chains_supported": list(CHAIN_PLUGINS.keys()),
        "policy": asdict(DEFAULT_POLICY),
        "ows_version": "1.0.0",
        "yield_only": True,
    }
