#!/usr/bin/env python3
"""Check that required environment variables are set before deployment."""

import os
import sys

REQUIRED = {
    "PRIVATE_KEY": "Wallet private key for deployments",
    "SEPOLIA_RPC_URL": "Sepolia testnet RPC URL",
    "SYNTHESIS_API_KEY": "Synthesis hackathon API key for track submission",
}

OPTIONAL = {
    "MAINNET_RPC_URL": "Ethereum mainnet RPC (mainnet deploy)",
    "ARBITRUM_RPC_URL": "Arbitrum RPC (NexusArbiter deploy)",
    "BASE_RPC_URL": "Base RPC (x402 payments)",
    "VENICE_API_KEY": "Venice API for private LLM reasoning",
    "BANKR_API_KEY": "Bankr LLM Gateway API key",
    "GROQ_API_KEY": "Groq fallback LLM API key",
    "ETHERSCAN_API_KEY": "Etherscan API for contract verification",
    "TELEGRAM_BOT_TOKEN": "Telegram bot for vault alerts",
    "AGENT_TREASURY_ADDRESS": "Deployed AgentTreasury contract address",
    "OLAS_MECH_KEY": "Olas marketplace key for nexus-scorer",
}

def check():
    missing = []
    for var, desc in REQUIRED.items():
        val = os.environ.get(var, "")
        if not val or val.startswith("your_"):
            missing.append((var, desc))

    optional_missing = []
    for var, desc in OPTIONAL.items():
        val = os.environ.get(var, "")
        if not val or val.startswith("your_"):
            optional_missing.append((var, desc))

    print("=== Nexus Environment Check ===\n")

    if missing:
        print("MISSING REQUIRED:")
        for var, desc in missing:
            print(f"  x {var}: {desc}")
        print()
    else:
        print("All required env vars set")
        print()

    if optional_missing:
        print("OPTIONAL (some features disabled):")
        for var, desc in optional_missing:
            print(f"  o {var}: {desc}")
        print()

    if missing:
        print("Set missing vars in .env and run: source .env")
        sys.exit(1)

    print("Ready to deploy!")

if __name__ == "__main__":
    check()
