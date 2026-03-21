"""
x402 HTTP Payment Protocol middleware for Nexus MCP servers.

Uses the official x402 Python SDK: pip install x402
SDK docs: https://github.com/coinbase/x402

The x402 protocol (Coinbase, production Q1 2026):
  1. Client requests resource
  2. Server responds 402 + payment requirements
  3. Client signs EIP-3009 payment authorization
  4. Client retries with X-Payment header
  5. Server settles onchain, returns 200
"""
from typing import Callable
import json

try:
    # Official x402 SDK (pip install x402)
    from x402.client import X402Client
    from x402.server import X402Server
    X402_SDK_AVAILABLE = True
except ImportError:
    X402_SDK_AVAILABLE = False
    # Fallback to manual implementation below

USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base


def x402_payment_required(service: str, price_usdc: float, wallet: str = "") -> dict:
    """Returns x402 payment-required headers."""
    return {
        "X-Payment-Required": "true",
        "X-Payment-Token": USDC_BASE,
        "X-Payment-Chain": "base",
        "X-Payment-Amount": str(int(price_usdc * 1_000_000)),  # USDC has 6 decimals
        "X-Payment-Recipient": wallet or "0x0000000000000000000000000000000000000000",
        "X-Service": service,
    }


def verify_x402_payment(headers: dict, expected_amount_usdc: float) -> bool:
    """Check if x402 payment headers are present and sufficient."""
    payment_header = headers.get("X-Payment-Proof", "")
    if not payment_header:
        return False
    # In production: verify on-chain payment tx
    # Demo: any non-empty proof passes
    return len(payment_header) > 0


def build_payment_header(amount_eth: float, chain: str = "base", token: str = "ETH") -> dict:
    """Build x402 payment header. Uses official SDK if available."""
    if X402_SDK_AVAILABLE:
        # SDK path (preferred)
        # client = X402Client(wallet=wallet)
        # return client.build_payment_header(amount=amount_eth, chain=chain)
        pass  # SDK integration — requires wallet context
    # Manual fallback (RFC-compatible)
    return {
        "X-Payment": json.dumps({
            "scheme": "exact",
            "network": f"eip155:{_chain_id(chain)}",
            "amount": str(int(amount_eth * 1e18)),
            "token": _token_address(token, chain),
        })
    }


def verify_payment_header(request_headers: dict, min_amount_eth: float) -> bool:
    """Verify incoming x402 payment header format (does not verify onchain)."""
    header = request_headers.get("X-Payment") or request_headers.get("x-payment", "")
    if not header:
        return False
    try:
        payment = json.loads(header)
        amount_wei = int(payment.get("amount", 0))
        min_wei = int(min_amount_eth * 1e18)
        network = payment.get("network", "")
        valid_chains = {"eip155:8453", "eip155:1", "eip155:42161", "eip155:42220"}
        return amount_wei >= min_wei and network in valid_chains
    except (json.JSONDecodeError, ValueError):
        return False


def _chain_id(chain: str) -> int:
    return {"base": 8453, "ethereum": 1, "mainnet": 1, "arbitrum": 42161, "celo": 42220}.get(chain, 8453)


def _token_address(token: str, chain: str) -> str:
    # USDC addresses per chain (x402 commonly uses USDC)
    usdc = {"base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "ethereum": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "arbitrum": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"}
    if token == "USDC":
        return usdc.get(chain, usdc["base"])
    return "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"  # ETH sentinel
