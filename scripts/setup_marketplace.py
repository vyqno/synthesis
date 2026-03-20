"""
Marketplace setup for Nexus — Locus, x402, Slice store configuration.
"""
import json, os, hashlib, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

LOCUS_API_KEY = os.getenv("LOCUS_API_KEY", "")
BASE_RPC = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")

def setup_locus_wallet():
    """Configure Locus wallet for Nexus on Base (USDC only)."""
    config = {
        "locus_wallet_id": f"nexus-{hashlib.sha256(b'nexus').hexdigest()[:8]}",
        "chain": "base",
        "asset": "USDC",
        "spending_controls": {
            "per_tx_cap_usd": 10.0,
            "daily_cap_usd": 50.0,
            "whitelist": ["bankr", "zyfai", "openserv"],
        },
        "status": "configured" if LOCUS_API_KEY else "demo_mode",
    }
    return config

def setup_x402_services():
    """Define x402-payable services for each MCP server."""
    return [
        {"service": "lido-mcp", "price_usdc": 0.01, "per": "call", "chain": "base"},
        {"service": "trade-mcp", "price_usdc": 0.05, "per": "swap", "chain": "base"},
        {"service": "goods-mcp", "price_usdc": 0.10, "per": "evaluation", "chain": "base"},
        {"service": "identity-mcp", "price_usdc": 0.001, "per": "lookup", "chain": "base"},
        {"service": "secrets-mcp", "price_usdc": 0.05, "per": "proof", "chain": "base"},
    ]

def setup_slice_store():
    """Configure Slice store for Nexus services on Base."""
    return {
        "store_name": "Nexus Agent Services",
        "chain": "base",
        "products": [
            {"name": "Public Goods Evaluation", "price_usd": 0.10, "mcp_tool": "score_public_good"},
            {"name": "ZK Proof Generation", "price_usd": 0.05, "mcp_tool": "generate_proof"},
            {"name": "Agent Coordination", "price_usd": 0.25, "mcp_tool": "dispatch_task"},
            {"name": "ENS Resolution", "price_usd": 0.001, "mcp_tool": "resolve_ens"},
        ],
        "hook": "NexusSliceHook.sol",
        "hook_description": "20% discount for high-reputation agents (ERC-8004 score >80)",
    }

if __name__ == "__main__":
    config = {
        "locus": setup_locus_wallet(),
        "x402_services": setup_x402_services(),
        "slice_store": setup_slice_store(),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out = Path("marketplace_config.json")
    out.write_text(json.dumps(config, indent=2))
    print(f"Written {out}")
    print(json.dumps(config, indent=2))
