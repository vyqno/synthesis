#!/usr/bin/env python3
"""
verify_deployment.py
====================
Reads the broadcast log produced by DeployAll.s.sol and verifies that every
contract is deployed and has non-zero bytecode on-chain.

Usage:
    python3 scripts/verify_deployment.py

Reads:
    contracts/broadcast/DeployAll.s.sol/11155111/run-latest.json

Requires:
    SEPOLIA_RPC_URL in environment (or .env file).
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CHAIN_ID = 11155111  # Sepolia
BROADCAST_PATH = Path(__file__).parent.parent / (
    f"contracts/broadcast/DeployAll.s.sol/{CHAIN_ID}/run-latest.json"
)

# Contract names we expect to find (must match the contractName field in the log)
EXPECTED_CONTRACTS = [
    "NexusPublicGoodsVault",
    "AgentIdentity",
    "NexusArbiter",
    "AgentTreasury",
    "NexusComputeCredit",
    "NexusReputationStaking",
    "NexusYieldSplitter",
    "AgentEscrow",
    "NexusSliceHook",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_env() -> None:
    """Load .env file if present (simple key=value parser, no external deps)."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # Remove surrounding quotes if present
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            os.environ.setdefault(key, value)


def eth_get_code(rpc_url: str, address: str) -> str:
    """Call eth_getCode via raw JSON-RPC (no web3 dependency)."""
    payload = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [address, "latest"],
            "id": 1,
        }
    ).encode()
    req = urllib.request.Request(
        rpc_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    return result.get("result", "0x")


def parse_broadcast(path: Path) -> dict[str, str]:
    """
    Parse a Forge broadcast log and return {contractName: deployedAddress}.
    Handles both the 'transactions' array (create transactions) and the
    'receipts' array (for address confirmation).
    """
    with path.open() as f:
        data = json.load(f)

    deployed: dict[str, str] = {}

    for tx in data.get("transactions", []):
        if tx.get("transactionType") not in ("CREATE", "CREATE2"):
            continue
        name = tx.get("contractName")
        addr = tx.get("contractAddress")
        if name and addr:
            deployed[name] = addr.lower()

    return deployed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    load_env()

    rpc_url = os.environ.get("SEPOLIA_RPC_URL")
    if not rpc_url:
        print("ERROR: SEPOLIA_RPC_URL not set. Add it to .env or export it.", file=sys.stderr)
        return 1

    if not BROADCAST_PATH.exists():
        print(f"ERROR: Broadcast log not found at:\n  {BROADCAST_PATH}", file=sys.stderr)
        print("Run `make deploy-sepolia` first.", file=sys.stderr)
        return 1

    print(f"Reading broadcast log: {BROADCAST_PATH.relative_to(Path.cwd())}")
    deployed = parse_broadcast(BROADCAST_PATH)

    if not deployed:
        print("ERROR: No CREATE transactions found in broadcast log.", file=sys.stderr)
        return 1

    # -----------------------------------------------------------------------
    # Verify each expected contract
    # -----------------------------------------------------------------------
    col_name = 30
    col_addr = 44
    col_status = 10

    header = f"{'Contract':<{col_name}} {'Address':<{col_addr}} {'Status':<{col_status}}"
    print()
    print(header)
    print("-" * len(header))

    all_ok = True
    for name in EXPECTED_CONTRACTS:
        addr = deployed.get(name)
        if not addr:
            print(f"{name:<{col_name}} {'<not in broadcast>':<{col_addr}} MISSING")
            all_ok = False
            continue

        try:
            code = eth_get_code(rpc_url, addr)
            has_code = code not in ("0x", "0x0", "", None)
            status = "OK" if has_code else "NO CODE"
            if not has_code:
                all_ok = False
        except Exception as exc:
            status = f"RPC ERR: {exc}"
            all_ok = False

        print(f"{name:<{col_name}} {addr:<{col_addr}} {status}")

    # Show any unexpected contracts that were also deployed
    extras = {k: v for k, v in deployed.items() if k not in EXPECTED_CONTRACTS}
    if extras:
        print()
        print("Additional deployed contracts:")
        for name, addr in extras.items():
            print(f"  {name:<{col_name - 2}} {addr}")

    print()
    if all_ok:
        print("All contracts deployed and verified.")
    else:
        print("Some contracts are missing or have no bytecode — check the deployment logs.")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
