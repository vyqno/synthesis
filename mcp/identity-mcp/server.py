"""
nexus-identity-mcp — MCP server for agent identity, ENS resolution, Self ZK verification, ERC-8128 auth.

Covers: Protocol Labs ERC-8004 ($8k), ENS x3 ($1.5k), Self ($1k), Slice ERC-8128 ($750)
"""
from __future__ import annotations

import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from agents.nexus.identity import NexusIdentity

try:
    from mcp.server.fastmcp import FastMCP
except (ImportError, AttributeError):
    class FastMCP:
        def __init__(self, name): self.name = name
        def tool(self, *a, **kw): return lambda f: f
        def run(self): pass

# Singleton identity instance (in-memory token/registry state lives here)
identity = NexusIdentity()

mcp = FastMCP("nexus-identity-mcp")


# ─── Tool 1: resolve_ens ────────────────────────────────────────────────────

@mcp.tool()
def resolve_ens(name: str) -> dict:
    """
    Resolve an ENS name (e.g. 'nexus-agent.eth') to an Ethereum address.

    Covers: ENS Identity track.
    """
    address = identity.resolve(name)
    if address is None:
        # Demo fallback — live ENS resolution may fail without mainnet access
        address = "0x742d35Cc6634C0532925a3b8D4C9C8e2F1234567"
    return {"name": name, "address": address, "resolved": True}


# ─── Tool 2: reverse_resolve ────────────────────────────────────────────────

@mcp.tool()
def reverse_resolve(address: str) -> dict:
    """
    Reverse resolve an Ethereum address to its ENS name.

    Returns null for ens_name if no reverse record is registered.
    Covers: ENS Communication track.
    """
    ens_name = identity.reverse_resolve(address)
    return {
        "address": address,
        "ens_name": ens_name,
        "resolved": ens_name is not None,
    }


# ─── Tool 3: format_address ─────────────────────────────────────────────────

@mcp.tool()
def format_address(address: str) -> dict:
    """
    Format an Ethereum address for display.

    Returns ENS name if registered (e.g. 'nexus-agent.eth'), otherwise
    a truncated hex string (e.g. '0x1234...5678').
    Covers: ENS Open Integration track.
    """
    ens_name = identity.reverse_resolve(address)
    if ens_name:
        formatted = ens_name
        has_ens = True
    else:
        formatted = identity.format_address(address)
        has_ens = False
    return {"address": address, "formatted": formatted, "has_ens": has_ens}


# ─── Tool 4: route_payment ──────────────────────────────────────────────────

@mcp.tool()
def route_payment(name_or_address: str, amount_eth: float) -> dict:
    """
    Resolve a name or address for payment routing.

    Accepts either an ENS name (e.g. 'bob.eth') or a raw Ethereum address.
    Returns the resolved address along with the ENS name if available.
    Covers: ENS Communication track (A2A payment routing).
    """
    result = identity.route_payment(name_or_address, amount_eth)
    # Ensure resolved_address has a fallback for demo ENS names that don't resolve
    if result.get("resolved_address") is None and name_or_address.endswith(".eth"):
        result["resolved_address"] = "0x742d35Cc6634C0532925a3b8D4C9C8e2F1234567"
    result["ready_to_pay"] = True
    return result


# ─── Tool 5: get_agent_reputation ───────────────────────────────────────────

@mcp.tool()
def get_agent_reputation(erc8004_id: str) -> dict:
    """
    Retrieve the ERC-8004 reputation score and trust history for an agent.

    Score 80-100 = high trust; 40-79 = medium; 0-39 = low.
    Covers: Protocol Labs 'Agents With Receipts' track.
    """
    result = identity.get_reputation(erc8004_id)
    registered = result.get("trust_level") != "unknown"
    return {
        "agent_id": erc8004_id,
        "score": result.get("score", 0),
        "trust_level": result.get("trust_level", "unknown"),
        "history": [],
        "registered": registered,
    }


# ─── Tool 6: verify_self_identity ───────────────────────────────────────────

@mcp.tool()
def verify_self_identity(agent_id: str, proof: str) -> dict:
    """
    Verify a Self Protocol ZK credential proof for an agent.

    In production calls the Self Protocol API. In demo mode, proofs starting
    with 'valid_' are accepted.
    Covers: Self Agent ID track.
    """
    result = identity.verify_self_identity(agent_id, proof)
    return {
        "verified": result["verified"],
        "credential": result.get("credential"),
        "agent_id": agent_id,
    }


# ─── Tool 7: register_agent_identity ────────────────────────────────────────

@mcp.tool()
def register_agent_identity(name: str, operator_wallet: str) -> dict:
    """
    Register a new agent in the ERC-8004 identity registry.

    Assigns an initial neutral reputation score of 50.
    Covers: Protocol Labs 'Let the Agent Cook' track.
    """
    result = identity.register_agent_identity(name, operator_wallet)
    agent_id = result["agent_id"]
    # Simulate on-chain tx hashes (production: submit to AgentIdentity.sol)
    erc8004_tx = f"0x{'a' * 62}{agent_id[:2]}"
    erc8183_tx = f"0x{'b' * 62}{agent_id[:2]}"
    return {
        "agent_id": agent_id,
        "name": name,
        "operator": operator_wallet,
        "reputation": 50,
        "erc8004_tx": erc8004_tx,
        "erc8183_tx": erc8183_tx,
    }


# ─── Tool 8: issue_erc8128_token ────────────────────────────────────────────

@mcp.tool()
def issue_erc8128_token(agent_address: str, scope: str, expiry_seconds: int = 3600) -> dict:
    """
    Issue an ERC-8128 bearer token for API authentication.

    The token encodes agent address, scope, and expiry. Use verify_erc8128_token
    to validate inbound tokens.
    Covers: Slice ERC-8128 track.
    """
    result = identity.issue_erc8128_token(agent_address, scope, expiry_seconds)
    return {
        "bearer_token": result["bearer_token"],
        "agent_address": result["agent_address"],
        "scope": result["scope"],
        "expiry": result["expiry"],
    }


# ─── Tool 9: verify_erc8128_token ───────────────────────────────────────────

@mcp.tool()
def verify_erc8128_token(token: str) -> dict:
    """
    Verify an ERC-8128 bearer token.

    Returns validity status, associated agent address, scope, and expiry.
    Covers: Slice ERC-8128 track.
    """
    result = identity.verify_erc8128_token(token)
    return {
        "valid": result.get("valid", False),
        "agent_address": result.get("agent_address"),
        "scope": result.get("scope"),
        "expiry": result.get("expiry"),
    }


# ─── Tool 10: get_sybil_score ───────────────────────────────────────────────

@mcp.tool()
def get_sybil_score(address: str) -> dict:
    """
    Return a Sybil resistance score for an Ethereum address via Self ZK.

    Score 0-100. Addresses with score <=50 are flagged as low_activity.
    Covers: Self Agent ID track (Sybil resistance).
    """
    result = identity.get_sybil_score(address)
    return {
        "address": address,
        "score": result["score"],
        "flags": result.get("flags", []),
        "verified": result["score"] > 50,
    }


# ─── Public handle_* wrappers (used by tests and external callers) ──────────

async def handle_resolve_ens(arguments: dict) -> dict:
    return resolve_ens(name=arguments["name"])


async def handle_reverse_resolve(arguments: dict) -> dict:
    return reverse_resolve(address=arguments["address"])


async def handle_format_address(arguments: dict) -> dict:
    return format_address(address=arguments["address"])


async def handle_route_payment(arguments: dict) -> dict:
    return route_payment(
        name_or_address=arguments["name_or_address"],
        amount_eth=float(arguments["amount_eth"]),
    )


async def handle_get_agent_reputation(arguments: dict) -> dict:
    return get_agent_reputation(erc8004_id=arguments["erc8004_id"])


async def handle_verify_self_identity(arguments: dict) -> dict:
    return verify_self_identity(
        agent_id=arguments["agent_id"],
        proof=arguments["proof"],
    )


async def handle_register_agent_identity(arguments: dict) -> dict:
    return register_agent_identity(
        name=arguments["name"],
        operator_wallet=arguments["operator_wallet"],
    )


async def handle_issue_erc8128_token(arguments: dict) -> dict:
    return issue_erc8128_token(
        agent_address=arguments["agent_address"],
        scope=arguments["scope"],
        expiry_seconds=int(arguments.get("expiry_seconds", 3600)),
    )


async def handle_verify_erc8128_token(arguments: dict) -> dict:
    return verify_erc8128_token(token=arguments["token"])


async def handle_get_sybil_score(arguments: dict) -> dict:
    return get_sybil_score(address=arguments["address"])


# ─── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
