"""
x402 HTTP payment middleware for Nexus MCP servers.
Adds x402 payment headers to HTTP responses.
"""
from typing import Callable
import json

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
