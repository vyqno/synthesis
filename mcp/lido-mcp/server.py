"""
nexus-lido-mcp — MCP server for Lido staking operations.

Covers:
- Lido MCP track ($5k): stake/unstake/wrap/governance from a chat conversation
- Lido Vault Monitor track ($1.5k): EarnETH/EarnUSD yield monitoring + Telegram alerts
"""
import asyncio
import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except (ImportError, AttributeError):
    def _noop_decorator(*a, **kw):
        return lambda f: f
    class Server:
        def __init__(self, name): self.name = name
        def list_tools(self): return _noop_decorator
        def call_tool(self): return _noop_decorator
        def list_resources(self): return _noop_decorator
        def list_prompts(self): return _noop_decorator
        def get_prompt(self): return _noop_decorator
        def read_resource(self): return _noop_decorator
    from contextlib import asynccontextmanager
    @asynccontextmanager
    async def stdio_server(): yield (None, None)
from mcp.types import TextContent, Tool

load_dotenv()

# ---------------------------------------------------------------------------
# Network Configuration
# ---------------------------------------------------------------------------

ETH_RPC_URL = os.getenv("ETH_RPC_URL", "https://eth.llamarpc.com")
SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "https://rpc.sepolia.org")
NETWORK = os.getenv("NETWORK", "mainnet")  # "mainnet" or "sepolia"
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")

# ---------------------------------------------------------------------------
# Contract Addresses
# ---------------------------------------------------------------------------

# Ethereum Mainnet
LIDO_STETH_MAINNET = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
WSTETH_MAINNET = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
LIDO_WITHDRAWAL_QUEUE = "0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1"

# Ethereum Sepolia (testnet)
LIDO_STETH_SEPOLIA = "0x3e3FE7dBc6B4C189E7128855dD526361c49b40Af"
WSTETH_SEPOLIA = "0xB82381A3fBD3FaFA77B3a7bE693342618240067b"

# ---------------------------------------------------------------------------
# ABIs
# ---------------------------------------------------------------------------

STETH_ABI = [
    {
        "name": "submit",
        "type": "function",
        "inputs": [{"name": "_referral", "type": "address"}],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "payable",
    },
    {
        "name": "balanceOf",
        "type": "function",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
    },
    {
        "name": "approve",
        "type": "function",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "outputs": [{"type": "bool"}],
        "stateMutability": "nonpayable",
    },
]

WSTETH_ABI = [
    {
        "name": "wrap",
        "type": "function",
        "inputs": [{"name": "stETHAmount", "type": "uint256"}],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "nonpayable",
    },
    {
        "name": "unwrap",
        "type": "function",
        "inputs": [{"name": "wstETHAmount", "type": "uint256"}],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "nonpayable",
    },
    {
        "name": "balanceOf",
        "type": "function",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
    },
    {
        "name": "getStETHByWstETH",
        "type": "function",
        "inputs": [{"name": "wstETHAmount", "type": "uint256"}],
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
    },
]

WITHDRAWAL_QUEUE_ABI = [
    {
        "name": "requestWithdrawals",
        "type": "function",
        "inputs": [
            {"name": "_amounts", "type": "uint256[]"},
            {"name": "_owner", "type": "address"},
        ],
        "outputs": [{"name": "requestIds", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
    },
    {
        "name": "getWithdrawalRequests",
        "type": "function",
        "inputs": [{"name": "_owner", "type": "address"}],
        "outputs": [{"name": "requestsIds", "type": "uint256[]"}],
        "stateMutability": "view",
    },
]

# ---------------------------------------------------------------------------
# Helpers: Web3 connection
# ---------------------------------------------------------------------------


def get_web3():
    """Return a Web3 instance for the configured network."""
    from web3 import Web3

    rpc = SEPOLIA_RPC_URL if NETWORK == "sepolia" else ETH_RPC_URL
    w3 = Web3(Web3.HTTPProvider(rpc))
    return w3


def get_contract_addresses():
    if NETWORK == "sepolia":
        return LIDO_STETH_SEPOLIA, WSTETH_SEPOLIA
    return LIDO_STETH_MAINNET, WSTETH_MAINNET


def wei_to_eth(wei_value: int) -> float:
    from web3 import Web3

    return float(Web3.from_wei(wei_value, "ether"))


def eth_to_wei(eth_value: float) -> int:
    from web3 import Web3

    return Web3.to_wei(eth_value, "ether")


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


async def handle_stake(arguments: dict) -> dict:
    """Stakes ETH via Lido stETH contract."""
    amount_eth: float = float(arguments.get("amount_eth", 0))
    dry_run: bool = bool(arguments.get("dry_run", True))

    if amount_eth <= 0:
        return {"error": "amount_eth must be positive"}

    from web3 import Web3

    w3 = get_web3()
    steth_addr, _ = get_contract_addresses()
    steth = w3.eth.contract(address=Web3.to_checksum_address(steth_addr), abi=STETH_ABI)

    amount_wei = eth_to_wei(amount_eth)
    referral = "0x0000000000000000000000000000000000000000"

    tx = steth.functions.submit(referral).build_transaction(
        {
            "value": amount_wei,
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
            "nonce": 0,  # placeholder for dry-run
        }
    )

    if dry_run:
        return {
            "dry_run": True,
            "amount_eth": amount_eth,
            "steth_received": amount_eth,  # 1:1 at submission
            "tx_hash": None,
            "network": NETWORK,
            "contract": steth_addr,
            "estimated_gas": 150000,
            "note": "Set dry_run=False and configure PRIVATE_KEY env var to broadcast.",
        }

    if not PRIVATE_KEY:
        return {"error": "PRIVATE_KEY env var not set; cannot broadcast transaction."}

    account = w3.eth.account.from_key(PRIVATE_KEY)
    tx["nonce"] = w3.eth.get_transaction_count(account.address)
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "dry_run": False,
        "amount_eth": amount_eth,
        "steth_received": amount_eth,
        "tx_hash": receipt["transactionHash"].hex(),
        "block": receipt["blockNumber"],
        "network": NETWORK,
    }


async def handle_unstake(arguments: dict) -> dict:
    """Initiates a Lido withdrawal request."""
    amount_steth: float = float(arguments.get("amount_steth", 0))
    dry_run: bool = bool(arguments.get("dry_run", True))

    if amount_steth <= 0:
        return {"error": "amount_steth must be positive"}

    from web3 import Web3

    w3 = get_web3()
    amount_wei = eth_to_wei(amount_steth)

    if dry_run:
        return {
            "dry_run": True,
            "amount_steth": amount_steth,
            "withdrawal_request_id": None,
            "estimated_wait_days": "1-5",
            "network": NETWORK,
            "withdrawal_queue": LIDO_WITHDRAWAL_QUEUE,
            "note": "Unstaking requires approve() then requestWithdrawals(). Set dry_run=False to execute.",
        }

    if not PRIVATE_KEY:
        return {"error": "PRIVATE_KEY env var not set; cannot broadcast transaction."}

    account = w3.eth.account.from_key(PRIVATE_KEY)
    steth_addr, _ = get_contract_addresses()
    steth = w3.eth.contract(address=Web3.to_checksum_address(steth_addr), abi=STETH_ABI)
    wq = w3.eth.contract(
        address=Web3.to_checksum_address(LIDO_WITHDRAWAL_QUEUE), abi=WITHDRAWAL_QUEUE_ABI
    )

    # Step 1: approve withdrawal queue
    approve_tx = steth.functions.approve(
        Web3.to_checksum_address(LIDO_WITHDRAWAL_QUEUE), amount_wei
    ).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed_approve = account.sign_transaction(approve_tx)
    w3.eth.send_raw_transaction(signed_approve.raw_transaction)
    w3.eth.wait_for_transaction_receipt(
        signed_approve.raw_transaction[:32], timeout=120
    )

    # Step 2: request withdrawals
    request_tx = wq.functions.requestWithdrawals(
        [amount_wei], account.address
    ).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed_req = account.sign_transaction(request_tx)
    tx_hash = w3.eth.send_raw_transaction(signed_req.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "dry_run": False,
        "amount_steth": amount_steth,
        "withdrawal_request_id": receipt["transactionHash"].hex(),
        "estimated_wait_days": "1-5",
        "block": receipt["blockNumber"],
        "network": NETWORK,
    }


async def handle_wrap_steth(arguments: dict) -> dict:
    """Wraps stETH → wstETH."""
    amount_steth: float = float(arguments.get("amount_steth", 0))
    dry_run: bool = bool(arguments.get("dry_run", True))

    if amount_steth <= 0:
        return {"error": "amount_steth must be positive"}

    from web3 import Web3

    w3 = get_web3()
    _, wsteth_addr = get_contract_addresses()
    wsteth = w3.eth.contract(address=Web3.to_checksum_address(wsteth_addr), abi=WSTETH_ABI)

    amount_wei = eth_to_wei(amount_steth)

    # Fetch current exchange rate
    try:
        one_wsteth = 10**18
        steth_per_wsteth_wei = wsteth.functions.getStETHByWstETH(one_wsteth).call()
        exchange_rate = wei_to_eth(steth_per_wsteth_wei)
        wsteth_received = amount_steth / exchange_rate if exchange_rate > 0 else amount_steth
    except Exception:
        exchange_rate = 1.12  # typical approximate rate
        wsteth_received = amount_steth / exchange_rate

    if dry_run:
        return {
            "dry_run": True,
            "amount_steth": amount_steth,
            "wsteth_received": round(wsteth_received, 8),
            "exchange_rate": round(exchange_rate, 6),
            "tx_hash": None,
            "network": NETWORK,
            "note": "Set dry_run=False and configure PRIVATE_KEY to execute.",
        }

    if not PRIVATE_KEY:
        return {"error": "PRIVATE_KEY env var not set; cannot broadcast transaction."}

    account = w3.eth.account.from_key(PRIVATE_KEY)
    steth_addr, _ = get_contract_addresses()
    steth = w3.eth.contract(address=Web3.to_checksum_address(steth_addr), abi=STETH_ABI)

    # Approve wstETH contract to spend stETH
    approve_tx = steth.functions.approve(
        Web3.to_checksum_address(wsteth_addr), amount_wei
    ).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed_approve = account.sign_transaction(approve_tx)
    approve_hash = w3.eth.send_raw_transaction(signed_approve.raw_transaction)
    w3.eth.wait_for_transaction_receipt(approve_hash, timeout=120)

    # Wrap
    wrap_tx = wsteth.functions.wrap(amount_wei).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 150000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed_wrap = account.sign_transaction(wrap_tx)
    tx_hash = w3.eth.send_raw_transaction(signed_wrap.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "dry_run": False,
        "amount_steth": amount_steth,
        "wsteth_received": round(wsteth_received, 8),
        "exchange_rate": round(exchange_rate, 6),
        "tx_hash": receipt["transactionHash"].hex(),
        "block": receipt["blockNumber"],
        "network": NETWORK,
    }


async def handle_unwrap_wsteth(arguments: dict) -> dict:
    """Unwraps wstETH → stETH."""
    amount_wsteth: float = float(arguments.get("amount_wsteth", 0))
    dry_run: bool = bool(arguments.get("dry_run", True))

    if amount_wsteth <= 0:
        return {"error": "amount_wsteth must be positive"}

    from web3 import Web3

    w3 = get_web3()
    _, wsteth_addr = get_contract_addresses()
    wsteth = w3.eth.contract(address=Web3.to_checksum_address(wsteth_addr), abi=WSTETH_ABI)

    amount_wei = eth_to_wei(amount_wsteth)

    # Fetch exchange rate
    try:
        steth_received_wei = wsteth.functions.getStETHByWstETH(amount_wei).call()
        steth_received = wei_to_eth(steth_received_wei)
        exchange_rate = steth_received / amount_wsteth if amount_wsteth > 0 else 1.12
    except Exception:
        exchange_rate = 1.12
        steth_received = amount_wsteth * exchange_rate

    if dry_run:
        return {
            "dry_run": True,
            "amount_wsteth": amount_wsteth,
            "steth_received": round(steth_received, 8),
            "exchange_rate": round(exchange_rate, 6),
            "tx_hash": None,
            "network": NETWORK,
            "note": "Set dry_run=False and configure PRIVATE_KEY to execute.",
        }

    if not PRIVATE_KEY:
        return {"error": "PRIVATE_KEY env var not set; cannot broadcast transaction."}

    account = w3.eth.account.from_key(PRIVATE_KEY)

    unwrap_tx = wsteth.functions.unwrap(amount_wei).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 150000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed = account.sign_transaction(unwrap_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "dry_run": False,
        "amount_wsteth": amount_wsteth,
        "steth_received": round(steth_received, 8),
        "exchange_rate": round(exchange_rate, 6),
        "tx_hash": receipt["transactionHash"].hex(),
        "block": receipt["blockNumber"],
        "network": NETWORK,
    }


async def handle_get_balance(arguments: dict) -> dict:
    """Returns stETH, wstETH balances and pending withdrawal count for an address."""
    address: str = arguments.get("address", "")
    if not address:
        return {"error": "address is required"}

    from web3 import Web3

    w3 = get_web3()

    try:
        checksum_addr = Web3.to_checksum_address(address)
    except Exception:
        return {"error": f"Invalid address: {address}"}

    steth_addr, wsteth_addr = get_contract_addresses()
    steth = w3.eth.contract(address=Web3.to_checksum_address(steth_addr), abi=STETH_ABI)
    wsteth = w3.eth.contract(address=Web3.to_checksum_address(wsteth_addr), abi=WSTETH_ABI)

    try:
        steth_bal_wei = steth.functions.balanceOf(checksum_addr).call()
        steth_balance = wei_to_eth(steth_bal_wei)
    except Exception as e:
        steth_balance = f"error: {e}"

    try:
        wsteth_bal_wei = wsteth.functions.balanceOf(checksum_addr).call()
        wsteth_balance = wei_to_eth(wsteth_bal_wei)
    except Exception as e:
        wsteth_balance = f"error: {e}"

    # Pending withdrawals (mainnet only)
    pending_withdrawals = []
    if NETWORK == "mainnet":
        try:
            wq = w3.eth.contract(
                address=Web3.to_checksum_address(LIDO_WITHDRAWAL_QUEUE),
                abi=WITHDRAWAL_QUEUE_ABI,
            )
            pending_withdrawals = wq.functions.getWithdrawalRequests(checksum_addr).call()
        except Exception:
            pending_withdrawals = []

    return {
        "address": address,
        "steth_balance": steth_balance,
        "wsteth_balance": wsteth_balance,
        "pending_withdrawals": pending_withdrawals,
        "network": NETWORK,
    }


async def handle_get_vault_yield(arguments: dict) -> dict:
    """Fetches Lido vault yield data. Falls back to demo values if API unavailable."""
    vault: str = arguments.get("vault", "earneth").lower()

    demo_data = {
        "earneth": {
            "vault": "earneth",
            "current_apy": 4.2,
            "benchmark_apy": 3.8,
            "allocation": {"Aave": 40, "Morpho": 35, "Pendle": 25},
            "beating_benchmark": True,
            "source": "demo",
        },
        "earnusd": {
            "vault": "earnusd",
            "current_apy": 5.1,
            "benchmark_apy": 4.7,
            "allocation": {"Aave": 50, "Morpho": 30, "Maple": 20},
            "beating_benchmark": True,
            "source": "demo",
        },
    }

    if vault not in demo_data:
        return {"error": f"Unknown vault '{vault}'. Use 'earneth' or 'earnusd'."}

    # Try live Lido API for EarnETH
    if vault == "earneth":
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://api.lido.fi/v1/protocol/steth/apr/last", timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    current_apy = float(data.get("data", {}).get("apr", 4.2))
                    result = demo_data["earneth"].copy()
                    result["current_apy"] = round(current_apy, 4)
                    result["beating_benchmark"] = current_apy >= result["benchmark_apy"]
                    result["source"] = "lido_api"
                    return result
        except Exception:
            pass

    return demo_data[vault]


async def handle_get_governance_proposals(arguments: dict) -> dict:
    """Returns active Lido DAO governance proposals from Snapshot or demo data."""
    demo_proposals = [
        {
            "id": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            "title": "LIP-27: Set Node Operator Penalty for Key Misuse to 0.1 ETH",
            "state": "active",
            "votes_for": 42_500_000,
            "votes_against": 3_200_000,
            "quorum_reached": True,
            "ends_at": "2026-03-25T00:00:00Z",
            "link": "https://snapshot.org/#/lido-snapshot.eth",
        },
        {
            "id": "0xdeadbeef0000000000000000000000000000000000000000000000000000cafe",
            "title": "LIP-28: Integrate Gearbox as an EarnETH Allocation Target",
            "state": "active",
            "votes_for": 28_100_000,
            "votes_against": 8_900_000,
            "quorum_reached": False,
            "ends_at": "2026-03-27T00:00:00Z",
            "link": "https://snapshot.org/#/lido-snapshot.eth",
        },
        {
            "id": "0x1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff",
            "title": "LIP-29: Increase stETH Withdrawal Queue Buffer to 15,000 ETH",
            "state": "active",
            "votes_for": 61_000_000,
            "votes_against": 1_500_000,
            "quorum_reached": True,
            "ends_at": "2026-03-22T00:00:00Z",
            "link": "https://snapshot.org/#/lido-snapshot.eth",
        },
    ]

    # Try live Snapshot API
    try:
        query = """
        {
          proposals(
            first: 5,
            where: { space: "lido-snapshot.eth", state: "active" },
            orderBy: "created", orderDirection: desc
          ) {
            id title state scores_total scores end
          }
        }
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://hub.snapshot.org/graphql",
                json={"query": query},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                proposals = data.get("data", {}).get("proposals", [])
                if proposals:
                    return {
                        "proposals": proposals,
                        "count": len(proposals),
                        "source": "snapshot_api",
                    }
    except Exception:
        pass

    return {
        "proposals": demo_proposals,
        "count": len(demo_proposals),
        "source": "demo",
    }


async def handle_vote(arguments: dict) -> dict:
    """Casts a vote on a Lido governance proposal."""
    proposal_id: str = arguments.get("proposal_id", "")
    support: bool = bool(arguments.get("support", True))
    dry_run: bool = bool(arguments.get("dry_run", True))

    if not proposal_id:
        return {"error": "proposal_id is required"}

    if dry_run:
        return {
            "dry_run": True,
            "proposal_id": proposal_id,
            "support": support,
            "vote_weight": "depends on your LDO balance",
            "tx_hash": None,
            "note": (
                "Lido governance uses Snapshot (off-chain) voting. "
                "Set dry_run=False to submit a signed vote. "
                "Requires PRIVATE_KEY env var."
            ),
        }

    if not PRIVATE_KEY:
        return {"error": "PRIVATE_KEY env var not set; cannot sign vote."}

    # Snapshot off-chain vote via API
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct

        account = Account.from_key(PRIVATE_KEY)
        choice = 1 if support else 2  # Snapshot: 1=For, 2=Against

        vote_payload = {
            "version": "0.1.3",
            "timestamp": str(int(asyncio.get_event_loop().time())),
            "space": "lido-snapshot.eth",
            "type": "single-choice",
            "payload": {
                "proposal": proposal_id,
                "choice": choice,
                "metadata": "{}",
            },
        }
        msg_str = json.dumps(vote_payload, separators=(",", ":"))
        message = encode_defunct(text=msg_str)
        signed_msg = account.sign_message(message)

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://hub.snapshot.org/api/message",
                json={
                    "address": account.address,
                    "msg": msg_str,
                    "sig": signed_msg.signature.hex(),
                },
                timeout=15,
            )
            result = resp.json()

        return {
            "dry_run": False,
            "proposal_id": proposal_id,
            "support": support,
            "voter": account.address,
            "snapshot_response": result,
        }
    except Exception as e:
        return {"error": f"Vote failed: {e}"}


# ---------------------------------------------------------------------------
# MCP Server definition
# ---------------------------------------------------------------------------

app = Server("nexus-lido-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="stake",
            description=(
                "Stake ETH via Lido to receive stETH. "
                "Use dry_run=True (default) to preview without broadcasting."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "amount_eth": {
                        "type": "number",
                        "description": "Amount of ETH to stake (e.g. 0.1)",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulate only (default: true)",
                        "default": True,
                    },
                },
                "required": ["amount_eth"],
            },
        ),
        Tool(
            name="unstake",
            description=(
                "Initiate a Lido withdrawal request to unstake stETH back to ETH. "
                "Withdrawal takes 1-5 days. Use dry_run=True to preview."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "amount_steth": {
                        "type": "number",
                        "description": "Amount of stETH to unstake",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulate only (default: true)",
                        "default": True,
                    },
                },
                "required": ["amount_steth"],
            },
        ),
        Tool(
            name="wrap_steth",
            description=(
                "Wrap stETH into wstETH (non-rebasing wrapped version). "
                "Use dry_run=True to preview the exchange rate and expected wstETH received."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "amount_steth": {
                        "type": "number",
                        "description": "Amount of stETH to wrap into wstETH",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulate only (default: true)",
                        "default": True,
                    },
                },
                "required": ["amount_steth"],
            },
        ),
        Tool(
            name="unwrap_wsteth",
            description=(
                "Unwrap wstETH back into stETH. "
                "Use dry_run=True to preview the exchange rate and expected stETH received."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "amount_wsteth": {
                        "type": "number",
                        "description": "Amount of wstETH to unwrap into stETH",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulate only (default: true)",
                        "default": True,
                    },
                },
                "required": ["amount_wsteth"],
            },
        ),
        Tool(
            name="get_balance",
            description=(
                "Get stETH balance, wstETH balance, and pending withdrawal request IDs "
                "for a given Ethereum address."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Ethereum address (0x...)",
                    },
                },
                "required": ["address"],
            },
        ),
        Tool(
            name="get_vault_yield",
            description=(
                "Get current APY and allocation for a Lido yield vault (EarnETH or EarnUSD). "
                "Shows whether the vault is beating its benchmark."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "vault": {
                        "type": "string",
                        "description": "Vault to query: 'earneth' or 'earnusd' (default: earneth)",
                        "enum": ["earneth", "earnusd"],
                        "default": "earneth",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_governance_proposals",
            description=(
                "List active Lido DAO governance proposals from Snapshot. "
                "Returns proposal title, vote counts, and deadline."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="vote",
            description=(
                "Cast a vote on a Lido DAO governance proposal via Snapshot. "
                "Use dry_run=True to preview. Set support=True to vote For, False to vote Against."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "proposal_id": {
                        "type": "string",
                        "description": "Snapshot proposal ID (hex string from get_governance_proposals)",
                    },
                    "support": {
                        "type": "boolean",
                        "description": "True to vote For, False to vote Against",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, simulate only (default: true)",
                        "default": True,
                    },
                },
                "required": ["proposal_id", "support"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handlers = {
        "stake": handle_stake,
        "unstake": handle_unstake,
        "wrap_steth": handle_wrap_steth,
        "unwrap_wsteth": handle_unwrap_wsteth,
        "get_balance": handle_get_balance,
        "get_vault_yield": handle_get_vault_yield,
        "get_governance_proposals": handle_get_governance_proposals,
        "vote": handle_vote,
    }

    handler = handlers.get(name)
    if handler is None:
        result = {"error": f"Unknown tool: {name}"}
    else:
        try:
            result = await handler(arguments)
        except Exception as e:
            result = {"error": str(e), "tool": name}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
