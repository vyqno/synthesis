"""
nexus-trade-mcp — MCP server for token swaps, perpetual positions, DCA, and portfolio management.

Covers: Uniswap ($5k), Base Autonomous Trading ($5k), bond.credit ($1.5k), MoonPay CLI ($3.5k)

IMPORTANT: GMX positions on Arbitrum must be REAL (no simulation) for bond.credit track.
Uniswap API key required: set UNISWAP_API_KEY env var.
"""

import asyncio
import json
import os
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

app = Server("nexus-trade-mcp")

# ── Constants ─────────────────────────────────────────────────────────────────

# Token addresses
TOKEN_ADDRESSES: dict[str, dict[str, str]] = {
    "ethereum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    },
    "base": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "WETH": "0x4200000000000000000000000000000000000006",
    },
    "arbitrum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
        "BTC": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
    },
}

# GMX v2 on Arbitrum
GMX_EXCHANGE_ROUTER = "0x69C527fC77291722b52649E45c838e41be8Bf5d5"
GMX_ROUTER = "0x7452c558d45f8afC8c83dAe62C3f8A5BE19c71f6"

# GMX market token addresses (ETH/USD, BTC/USD, ARB/USD)
GMX_MARKETS: dict[str, str] = {
    "ETH/USD": "0x70d95587d40A2caf56bd97485aB3Eec10Bee6336",
    "BTC/USD": "0x47c031236e19d024b42f8AE6780E44A573170703",
    "ARB/USD": "0xC25cEf6061Cf5dE5eb761b50E4743c1F5D7E5407",
}

# Mock price feeds (used for demo/dry-run when no RPC available)
_DEMO_PRICES: dict[str, float] = {
    "ETH": 2400.0,
    "BTC": 65000.0,
    "ARB": 1.20,
    "USDC": 1.0,
    "WETH": 2400.0,
}

# ── File paths ─────────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
DCA_STATE_FILE = _HERE / "dca_schedules.json"

# ── DCA state helpers ──────────────────────────────────────────────────────────


def _load_dca_schedules() -> list[dict]:
    if DCA_STATE_FILE.exists():
        try:
            return json.loads(DCA_STATE_FILE.read_text())
        except Exception:
            pass
    return []


def _save_dca_schedules(schedules: list[dict]) -> None:
    DCA_STATE_FILE.write_text(json.dumps(schedules, indent=2))


# ── MoonPay CLI helper ─────────────────────────────────────────────────────────


def run_moonpay_cli(command: list[str]) -> dict:
    """Run MoonPay CLI command. Falls back to demo if not installed."""
    try:
        result = subprocess.run(
            ["npx", "@moonpay/cli"] + command,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    # Demo fallback
    return {
        "demo": True,
        "command": command,
        "note": "MoonPay CLI not installed — install with npm",
    }


# ── Uniswap API helper ─────────────────────────────────────────────────────────


async def _fetch_uniswap_quote(
    token_in: str,
    token_out: str,
    amount: float,
    chain: str,
) -> dict | None:
    """Call Uniswap Developer Platform API. Returns None on failure."""
    api_key = os.environ.get("UNISWAP_API_KEY", "")
    if not api_key:
        return None
    try:
        import httpx

        chain_id_map = {"ethereum": 1, "base": 8453, "arbitrum": 42161}
        chain_id = chain_id_map.get(chain, 1)

        # Resolve token addresses
        token_in_addr = TOKEN_ADDRESSES.get(chain, {}).get(
            token_in.upper(), token_in
        )
        token_out_addr = TOKEN_ADDRESSES.get(chain, {}).get(
            token_out.upper(), token_out
        )

        # Convert amount to smallest unit (use 18 decimals for ETH/WETH, 6 for USDC)
        decimals_in = 6 if token_in.upper() in ("USDC", "USDT") else 18
        amount_wei = int(amount * (10**decimals_in))

        payload = {
            "tokenInAddress": token_in_addr,
            "tokenOutAddress": token_out_addr,
            "tokenInChainId": chain_id,
            "tokenOutChainId": chain_id,
            "amount": str(amount_wei),
            "type": "EXACT_INPUT",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.uniswap.org/v1/quote",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        pass
    return None


def _demo_quote(
    token_in: str,
    token_out: str,
    amount: float,
    chain: str,
) -> dict:
    """Return a plausible demo quote when Uniswap API is unavailable."""
    price_in = _DEMO_PRICES.get(token_in.upper(), 1.0)
    price_out = _DEMO_PRICES.get(token_out.upper(), 1.0)
    amount_out = round(amount * price_in / price_out, 6)
    return {
        "token_in": token_in,
        "token_out": token_out,
        "amount_in": amount,
        "amount_out": amount_out,
        "price_impact": 0.05,
        "route": [f"{token_in}/{token_out}"],
        "gas_estimate": 150000,
        "chain": chain,
        "demo": True,
        "note": "Demo quote — set UNISWAP_API_KEY for live quotes",
    }


# ── Tool list ──────────────────────────────────────────────────────────────────


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_quote",
            description=(
                "Get a price quote for swapping tokens via Uniswap. "
                "Uses UNISWAP_API_KEY for live quotes; falls back to demo quote if unavailable. "
                "Returns amount_out, price_impact, route, and gas estimate."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token_in": {
                        "type": "string",
                        "description": "Input token symbol or address (e.g. ETH, USDC)",
                    },
                    "token_out": {
                        "type": "string",
                        "description": "Output token symbol or address (e.g. USDC, ETH)",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount of token_in to quote",
                    },
                    "chain": {
                        "type": "string",
                        "description": "Chain name: ethereum, base, or arbitrum (default: ethereum)",
                        "default": "ethereum",
                    },
                },
                "required": ["token_in", "token_out", "amount"],
            },
        ),
        Tool(
            name="swap",
            description=(
                "Execute a Uniswap v3 token swap. "
                "Use dry_run=True (default) to preview without executing. "
                "Set dry_run=False to build, sign, and broadcast the transaction. "
                "Requires PRIVATE_KEY env var for live execution."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token_in": {
                        "type": "string",
                        "description": "Input token symbol or address",
                    },
                    "token_out": {
                        "type": "string",
                        "description": "Output token symbol or address",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount of token_in to swap",
                    },
                    "slippage": {
                        "type": "number",
                        "description": "Slippage tolerance as percentage (default: 0.5)",
                        "default": 0.5,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true (default), preview only — no on-chain execution",
                        "default": True,
                    },
                    "chain": {
                        "type": "string",
                        "description": "Chain name: ethereum, base, or arbitrum (default: base)",
                        "default": "base",
                    },
                },
                "required": ["token_in", "token_out", "amount"],
            },
        ),
        Tool(
            name="open_gmx_position",
            description=(
                "Open a GMX v2 perpetual position on Arbitrum. "
                "Markets: ETH/USD, BTC/USD, ARB/USD. "
                "IMPORTANT: dry_run=False submits a REAL on-chain trade (required for bond.credit track). "
                "Requires PRIVATE_KEY and ARBITRUM_RPC_URL env vars for live execution."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "market": {
                        "type": "string",
                        "description": "Market pair: ETH/USD, BTC/USD, or ARB/USD",
                    },
                    "size_usd": {
                        "type": "number",
                        "description": "Position size in USD",
                    },
                    "direction": {
                        "type": "string",
                        "description": "Trade direction: long or short",
                        "enum": ["long", "short"],
                    },
                    "leverage": {
                        "type": "number",
                        "description": "Leverage multiplier (default: 2.0, max: 50)",
                        "default": 2.0,
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true (default), simulate — do not submit on-chain",
                        "default": True,
                    },
                },
                "required": ["market", "size_usd", "direction"],
            },
        ),
        Tool(
            name="get_gmx_positions",
            description=(
                "List open GMX perpetual positions with current PnL. "
                "Defaults to agent wallet if address not provided."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Wallet address to query (defaults to agent wallet from WALLET_ADDRESS env var)",
                        "default": "",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="close_gmx_position",
            description=(
                "Close an open GMX perpetual position. "
                "Use dry_run=True to preview PnL before closing. "
                "Set dry_run=False to submit the close order on-chain."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "position_id": {
                        "type": "string",
                        "description": "Position ID returned by open_gmx_position or get_gmx_positions",
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true (default), preview only — no on-chain execution",
                        "default": True,
                    },
                },
                "required": ["position_id"],
            },
        ),
        Tool(
            name="dca",
            description=(
                "Set up a Dollar Cost Averaging schedule for recurring token purchases. "
                "Uses MoonPay CLI if installed; otherwise stores schedule locally for nexus-monitor to execute. "
                "Default frequency is weekly (168 hours)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Token to buy (e.g. ETH, BTC, USDC)",
                    },
                    "amount_usd": {
                        "type": "number",
                        "description": "USD amount to spend per interval",
                    },
                    "frequency_hours": {
                        "type": "integer",
                        "description": "How often to execute in hours (default: 168 = weekly)",
                        "default": 168,
                    },
                },
                "required": ["token", "amount_usd"],
            },
        ),
        Tool(
            name="bridge",
            description=(
                "Bridge tokens between chains via MoonPay CLI. "
                "Supports ethereum, base, arbitrum, optimism, polygon. "
                "Returns tx_hash and estimated bridge time."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Token symbol to bridge (e.g. USDC, ETH)",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to bridge",
                    },
                    "from_chain": {
                        "type": "string",
                        "description": "Source chain name",
                    },
                    "to_chain": {
                        "type": "string",
                        "description": "Destination chain name",
                    },
                },
                "required": ["token", "amount", "from_chain", "to_chain"],
            },
        ),
        Tool(
            name="get_portfolio",
            description=(
                "Return token balances and USD values across all chains. "
                "Queries ETH and major ERC-20 balances via chain RPCs. "
                "Defaults to agent wallet if address not provided."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Wallet address to query (defaults to agent wallet from WALLET_ADDRESS env var)",
                        "default": "",
                    },
                },
                "required": [],
            },
        ),
    ]


# ── Tool dispatcher ────────────────────────────────────────────────────────────


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    result = await _dispatch(name, arguments)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "get_quote":
        return await _get_quote(args)
    if name == "swap":
        return await _swap(args)
    if name == "open_gmx_position":
        return await _open_gmx_position(args)
    if name == "get_gmx_positions":
        return await _get_gmx_positions(args)
    if name == "close_gmx_position":
        return await _close_gmx_position(args)
    if name == "dca":
        return _dca(args)
    if name == "bridge":
        return _bridge(args)
    if name == "get_portfolio":
        return await _get_portfolio(args)
    return {"error": f"Unknown tool: {name}"}


# ── Tool 1: get_quote ──────────────────────────────────────────────────────────


async def _get_quote(args: dict) -> dict:
    token_in: str = args["token_in"]
    token_out: str = args["token_out"]
    amount: float = float(args["amount"])
    chain: str = args.get("chain", "ethereum")

    api_data = await _fetch_uniswap_quote(token_in, token_out, amount, chain)
    if api_data:
        decimals_out = 6 if token_out.upper() in ("USDC", "USDT") else 18
        raw_out = int(api_data.get("quote", {}).get("amount", 0) or 0)
        amount_out = round(raw_out / (10**decimals_out), 6)
        return {
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount,
            "amount_out": amount_out,
            "price_impact": api_data.get("priceImpact", 0.0),
            "route": api_data.get("route", []),
            "gas_estimate": api_data.get("gasUseEstimate", 150000),
            "chain": chain,
            "source": "uniswap_api",
        }

    # Fallback to demo quote
    return _demo_quote(token_in, token_out, amount, chain)


# ── Tool 2: swap ──────────────────────────────────────────────────────────────


async def _swap(args: dict) -> dict:
    token_in: str = args["token_in"]
    token_out: str = args["token_out"]
    amount: float = float(args["amount"])
    slippage: float = float(args.get("slippage", 0.5))
    dry_run: bool = bool(args.get("dry_run", True))
    chain: str = args.get("chain", "base")

    quote = await _get_quote(
        {"token_in": token_in, "token_out": token_out, "amount": amount, "chain": chain}
    )
    amount_out = quote.get("amount_out", 0.0)
    min_amount_out = round(amount_out * (1 - slippage / 100), 6)

    if dry_run:
        return {
            "tx_hash": None,
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount,
            "amount_out": amount_out,
            "min_amount_out": min_amount_out,
            "slippage_percent": slippage,
            "chain": chain,
            "dry_run": True,
            "note": "Dry run — set dry_run=False to execute on-chain",
        }

    # Live execution path
    private_key = os.environ.get("PRIVATE_KEY", "")
    rpc_map = {
        "ethereum": os.environ.get("ETHEREUM_RPC_URL", "https://eth.llamarpc.com"),
        "base": os.environ.get("BASE_RPC_URL", "https://mainnet.base.org"),
        "arbitrum": os.environ.get("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
    }
    rpc_url = rpc_map.get(chain, rpc_map["base"])

    if not private_key:
        return {
            "error": "PRIVATE_KEY env var not set — cannot execute swap",
            "dry_run": False,
        }

    try:
        from eth_account import Account
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(private_key)

        token_in_addr = TOKEN_ADDRESSES.get(chain, {}).get(token_in.upper(), token_in)
        token_out_addr = TOKEN_ADDRESSES.get(chain, {}).get(token_out.upper(), token_out)

        # Uniswap v3 SwapRouter02 addresses by chain
        router_addresses = {
            "ethereum": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
            "base": "0x2626664c2603336E57B271c5C0b26F421741e481",
            "arbitrum": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",
        }
        router_addr = router_addresses.get(chain, router_addresses["base"])

        # ABI for exactInputSingle
        swap_abi = [
            {
                "name": "exactInputSingle",
                "type": "function",
                "inputs": [
                    {
                        "name": "params",
                        "type": "tuple",
                        "components": [
                            {"name": "tokenIn", "type": "address"},
                            {"name": "tokenOut", "type": "address"},
                            {"name": "fee", "type": "uint24"},
                            {"name": "recipient", "type": "address"},
                            {"name": "amountIn", "type": "uint256"},
                            {"name": "amountOutMinimum", "type": "uint256"},
                            {"name": "sqrtPriceLimitX96", "type": "uint160"},
                        ],
                    }
                ],
                "outputs": [{"name": "amountOut", "type": "uint256"}],
                "stateMutability": "payable",
            }
        ]

        router = w3.eth.contract(
            address=Web3.to_checksum_address(router_addr), abi=swap_abi
        )

        decimals_in = 6 if token_in.upper() in ("USDC", "USDT") else 18
        decimals_out = 6 if token_out.upper() in ("USDC", "USDT") else 18
        amount_in_wei = int(amount * (10**decimals_in))
        min_out_wei = int(min_amount_out * (10**decimals_out))

        params = (
            Web3.to_checksum_address(token_in_addr),
            Web3.to_checksum_address(token_out_addr),
            3000,  # 0.3% fee tier
            account.address,
            amount_in_wei,
            min_out_wei,
            0,  # sqrtPriceLimitX96
        )

        is_eth_in = token_in.upper() in ("ETH", "NATIVE")
        tx = router.functions.exactInputSingle(params).build_transaction(
            {
                "from": account.address,
                "value": amount_in_wei if is_eth_in else 0,
                "gas": 300000,
                "nonce": w3.eth.get_transaction_count(account.address),
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
            }
        )

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            "tx_hash": tx_hash.hex(),
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount,
            "amount_out": amount_out,
            "chain": chain,
            "status": "success" if receipt.status == 1 else "failed",
            "block": receipt.blockNumber,
            "dry_run": False,
        }

    except Exception as exc:
        return {
            "error": str(exc),
            "token_in": token_in,
            "token_out": token_out,
            "amount_in": amount,
            "chain": chain,
            "dry_run": False,
        }


# ── Tool 3: open_gmx_position ──────────────────────────────────────────────────


async def _open_gmx_position(args: dict) -> dict:
    market: str = args["market"]
    size_usd: float = float(args["size_usd"])
    direction: str = args["direction"].lower()
    leverage: float = float(args.get("leverage", 2.0))
    dry_run: bool = bool(args.get("dry_run", True))

    if market not in GMX_MARKETS:
        return {
            "error": f"Unknown market: {market}. Valid: {list(GMX_MARKETS.keys())}"
        }

    base_token = market.split("/")[0]
    entry_price = _DEMO_PRICES.get(base_token, 1.0)
    collateral_usd = size_usd / leverage
    liquidation_offset = collateral_usd * 0.8 / (size_usd / entry_price)

    if direction == "long":
        liquidation_price = round(entry_price - liquidation_offset, 2)
    else:
        liquidation_price = round(entry_price + liquidation_offset, 2)

    position_id = f"gmx-{direction}-{base_token}-{int(time.time())}"

    if dry_run:
        return {
            "position_id": position_id,
            "market": market,
            "size_usd": size_usd,
            "collateral_usd": round(collateral_usd, 2),
            "direction": direction,
            "leverage": leverage,
            "entry_price": entry_price,
            "liquidation_price": liquidation_price,
            "market_token": GMX_MARKETS[market],
            "dry_run": True,
            "note": "Dry run — set dry_run=False to submit real on-chain trade",
        }

    # Live execution — real on-chain GMX trade (required for bond.credit track)
    private_key = os.environ.get("PRIVATE_KEY", "")
    rpc_url = os.environ.get("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")

    if not private_key:
        return {
            "error": "PRIVATE_KEY env var not set — cannot open GMX position",
            "dry_run": False,
        }

    try:
        from eth_account import Account
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(private_key)

        # GMX Exchange Router ABI (createOrder)
        exchange_router_abi = [
            {
                "name": "createOrder",
                "type": "function",
                "inputs": [
                    {
                        "name": "params",
                        "type": "tuple",
                        "components": [
                            {
                                "name": "addresses",
                                "type": "tuple",
                                "components": [
                                    {"name": "receiver", "type": "address"},
                                    {"name": "callbackContract", "type": "address"},
                                    {"name": "uiFeeReceiver", "type": "address"},
                                    {"name": "market", "type": "address"},
                                    {"name": "initialCollateralToken", "type": "address"},
                                    {"name": "swapPath", "type": "address[]"},
                                ],
                            },
                            {
                                "name": "numbers",
                                "type": "tuple",
                                "components": [
                                    {"name": "sizeDeltaUsd", "type": "uint256"},
                                    {"name": "initialCollateralDeltaAmount", "type": "uint256"},
                                    {"name": "triggerPrice", "type": "uint256"},
                                    {"name": "acceptablePrice", "type": "uint256"},
                                    {"name": "executionFee", "type": "uint256"},
                                    {"name": "callbackGasLimit", "type": "uint256"},
                                    {"name": "minOutputAmount", "type": "uint256"},
                                ],
                            },
                            {"name": "orderType", "type": "uint8"},
                            {"name": "decreasePositionSwapType", "type": "uint8"},
                            {"name": "isLong", "type": "bool"},
                            {"name": "shouldUnwrapNativeToken", "type": "bool"},
                            {"name": "referralCode", "type": "bytes32"},
                        ],
                    }
                ],
                "outputs": [{"name": "", "type": "bytes32"}],
                "stateMutability": "payable",
            }
        ]

        exchange_router = w3.eth.contract(
            address=Web3.to_checksum_address(GMX_EXCHANGE_ROUTER),
            abi=exchange_router_abi,
        )

        market_addr = Web3.to_checksum_address(GMX_MARKETS[market])
        # Use USDC as collateral on Arbitrum
        collateral_token = Web3.to_checksum_address(
            TOKEN_ADDRESSES["arbitrum"]["USDC"]
        )
        execution_fee = w3.to_wei(0.001, "ether")  # ~$2-3 at current ETH prices
        size_delta_usd_scaled = int(size_usd * 10**30)  # GMX uses 30-decimal USD
        collateral_amount = int(collateral_usd * 10**6)  # USDC 6 decimals

        # Acceptable price: 1% slippage from entry
        if direction == "long":
            acceptable_price = int(entry_price * 1.01 * 10**30)
        else:
            acceptable_price = int(entry_price * 0.99 * 10**30)

        addresses_params = (
            account.address,  # receiver
            "0x0000000000000000000000000000000000000000",  # callbackContract
            "0x0000000000000000000000000000000000000000",  # uiFeeReceiver
            market_addr,
            collateral_token,
            [],  # swapPath
        )
        numbers_params = (
            size_delta_usd_scaled,
            collateral_amount,
            0,  # triggerPrice (market order)
            acceptable_price,
            execution_fee,
            0,  # callbackGasLimit
            0,  # minOutputAmount
        )

        order_type = 2  # MarketIncrease
        is_long = direction == "long"

        order_params = (
            addresses_params,
            numbers_params,
            order_type,
            0,  # decreasePositionSwapType
            is_long,
            True,  # shouldUnwrapNativeToken
            b"\x00" * 32,  # referralCode
        )

        tx = exchange_router.functions.createOrder(order_params).build_transaction(
            {
                "from": account.address,
                "value": execution_fee,
                "gas": 500000,
                "nonce": w3.eth.get_transaction_count(account.address),
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
            }
        )

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            "position_id": position_id,
            "market": market,
            "size_usd": size_usd,
            "collateral_usd": round(collateral_usd, 2),
            "direction": direction,
            "leverage": leverage,
            "entry_price": entry_price,
            "liquidation_price": liquidation_price,
            "tx_hash": tx_hash.hex(),
            "block": receipt.blockNumber,
            "status": "success" if receipt.status == 1 else "failed",
            "arbitrum_explorer": f"https://arbiscan.io/tx/{tx_hash.hex()}",
            "dry_run": False,
            "bond_credit_note": "Real on-chain GMX trade — qualifies for bond.credit track",
        }

    except Exception as exc:
        return {
            "error": str(exc),
            "market": market,
            "size_usd": size_usd,
            "direction": direction,
            "dry_run": False,
        }


# ── Tool 4: get_gmx_positions ─────────────────────────────────────────────────


async def _get_gmx_positions(args: dict) -> list[dict]:
    address: str = args.get("address", "") or os.environ.get("WALLET_ADDRESS", "")
    rpc_url = os.environ.get("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")

    if not address:
        return [{"error": "No address provided and WALLET_ADDRESS env var not set"}]

    try:
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(rpc_url))

        # GMX v2 Reader contract for position queries
        reader_addr = "0xf60becbba223EEA9495Da3f606753867eC10d139"
        data_store_addr = "0xFD70de6b91282D8017aA4E741e9Ae325CAb992d8"

        reader_abi = [
            {
                "name": "getAccountPositions",
                "type": "function",
                "inputs": [
                    {"name": "dataStore", "type": "address"},
                    {"name": "account", "type": "address"},
                    {"name": "start", "type": "uint256"},
                    {"name": "end", "type": "uint256"},
                ],
                "outputs": [
                    {
                        "name": "",
                        "type": "tuple[]",
                        "components": [
                            {
                                "name": "addresses",
                                "type": "tuple",
                                "components": [
                                    {"name": "account", "type": "address"},
                                    {"name": "market", "type": "address"},
                                    {"name": "collateralToken", "type": "address"},
                                ],
                            },
                            {
                                "name": "numbers",
                                "type": "tuple",
                                "components": [
                                    {"name": "sizeInUsd", "type": "uint256"},
                                    {"name": "sizeInTokens", "type": "uint256"},
                                    {"name": "collateralAmount", "type": "uint256"},
                                    {"name": "borrowingFactor", "type": "uint256"},
                                    {"name": "fundingFeeAmountPerSize", "type": "uint256"},
                                    {"name": "longTokenClaimableFundingAmountPerSize", "type": "uint256"},
                                    {"name": "shortTokenClaimableFundingAmountPerSize", "type": "uint256"},
                                    {"name": "increasedAtBlock", "type": "uint256"},
                                    {"name": "decreasedAtBlock", "type": "uint256"},
                                ],
                            },
                            {"name": "flags", "type": "tuple", "components": [
                                {"name": "isLong", "type": "bool"}
                            ]},
                        ],
                    }
                ],
                "stateMutability": "view",
            }
        ]

        reader = w3.eth.contract(
            address=Web3.to_checksum_address(reader_addr), abi=reader_abi
        )
        positions_raw = reader.functions.getAccountPositions(
            Web3.to_checksum_address(data_store_addr),
            Web3.to_checksum_address(address),
            0,
            20,
        ).call()

        # Reverse lookup market address -> name
        market_name_map = {v: k for k, v in GMX_MARKETS.items()}

        results = []
        for pos in positions_raw:
            addr_info = pos[0]
            num_info = pos[1]
            flags = pos[2]

            market_addr = addr_info[1].lower()
            market_name = market_name_map.get(
                Web3.to_checksum_address(market_addr), market_addr
            )
            size_usd = num_info[0] / 10**30
            collateral = num_info[2] / 10**6  # USDC
            is_long = flags[0]

            base_token = market_name.split("/")[0] if "/" in market_name else "ETH"
            current_price = _DEMO_PRICES.get(base_token, 1.0)

            # Simplified PnL estimate (no oracle integration in demo)
            pnl_usd = 0.0
            pnl_percent = 0.0

            results.append(
                {
                    "position_id": f"gmx-{'long' if is_long else 'short'}-{base_token}-{addr_info[1][:8]}",
                    "market": market_name,
                    "size_usd": round(size_usd, 2),
                    "collateral_usd": round(collateral, 2),
                    "direction": "long" if is_long else "short",
                    "entry_price": None,  # requires oracle data
                    "current_price": current_price,
                    "pnl_usd": round(pnl_usd, 2),
                    "pnl_percent": round(pnl_percent, 2),
                }
            )
        return results if results else [{"message": "No open positions found", "address": address}]

    except Exception as exc:
        return [
            {
                "error": str(exc),
                "address": address,
                "note": "Set ARBITRUM_RPC_URL env var for live position data",
            }
        ]


# ── Tool 5: close_gmx_position ────────────────────────────────────────────────


async def _close_gmx_position(args: dict) -> dict:
    position_id: str = args["position_id"]
    dry_run: bool = bool(args.get("dry_run", True))

    if dry_run:
        return {
            "position_id": position_id,
            "realized_pnl_usd": 0.0,
            "tx_hash": None,
            "dry_run": True,
            "note": "Dry run — set dry_run=False to submit close order on-chain",
        }

    private_key = os.environ.get("PRIVATE_KEY", "")
    rpc_url = os.environ.get("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")

    if not private_key:
        return {
            "error": "PRIVATE_KEY env var not set — cannot close GMX position",
            "position_id": position_id,
            "dry_run": False,
        }

    try:
        from eth_account import Account
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = Account.from_key(private_key)

        # Parse position_id to extract market info
        parts = position_id.split("-")
        direction = parts[1] if len(parts) > 1 else "long"
        base_token = parts[2] if len(parts) > 2 else "ETH"
        market_name = f"{base_token}/USD"
        market_addr = GMX_MARKETS.get(market_name, GMX_MARKETS["ETH/USD"])

        exchange_router_abi = [
            {
                "name": "createOrder",
                "type": "function",
                "inputs": [
                    {
                        "name": "params",
                        "type": "tuple",
                        "components": [
                            {
                                "name": "addresses",
                                "type": "tuple",
                                "components": [
                                    {"name": "receiver", "type": "address"},
                                    {"name": "callbackContract", "type": "address"},
                                    {"name": "uiFeeReceiver", "type": "address"},
                                    {"name": "market", "type": "address"},
                                    {"name": "initialCollateralToken", "type": "address"},
                                    {"name": "swapPath", "type": "address[]"},
                                ],
                            },
                            {
                                "name": "numbers",
                                "type": "tuple",
                                "components": [
                                    {"name": "sizeDeltaUsd", "type": "uint256"},
                                    {"name": "initialCollateralDeltaAmount", "type": "uint256"},
                                    {"name": "triggerPrice", "type": "uint256"},
                                    {"name": "acceptablePrice", "type": "uint256"},
                                    {"name": "executionFee", "type": "uint256"},
                                    {"name": "callbackGasLimit", "type": "uint256"},
                                    {"name": "minOutputAmount", "type": "uint256"},
                                ],
                            },
                            {"name": "orderType", "type": "uint8"},
                            {"name": "decreasePositionSwapType", "type": "uint8"},
                            {"name": "isLong", "type": "bool"},
                            {"name": "shouldUnwrapNativeToken", "type": "bool"},
                            {"name": "referralCode", "type": "bytes32"},
                        ],
                    }
                ],
                "outputs": [{"name": "", "type": "bytes32"}],
                "stateMutability": "payable",
            }
        ]

        exchange_router = w3.eth.contract(
            address=Web3.to_checksum_address(GMX_EXCHANGE_ROUTER),
            abi=exchange_router_abi,
        )

        entry_price = _DEMO_PRICES.get(base_token, 2400.0)
        execution_fee = w3.to_wei(0.001, "ether")
        is_long = direction == "long"

        # Close at market: use MaxUint for sizeDeltaUsd to close entire position
        if is_long:
            acceptable_price = int(entry_price * 0.99 * 10**30)
        else:
            acceptable_price = int(entry_price * 1.01 * 10**30)

        collateral_token = Web3.to_checksum_address(
            TOKEN_ADDRESSES["arbitrum"]["USDC"]
        )

        addresses_params = (
            account.address,
            "0x0000000000000000000000000000000000000000",
            "0x0000000000000000000000000000000000000000",
            Web3.to_checksum_address(market_addr),
            collateral_token,
            [],
        )
        numbers_params = (
            2**256 - 1,  # close entire position
            0,
            0,
            acceptable_price,
            execution_fee,
            0,
            0,
        )

        order_params = (
            addresses_params,
            numbers_params,
            3,  # MarketDecrease
            0,
            is_long,
            True,
            b"\x00" * 32,
        )

        tx = exchange_router.functions.createOrder(order_params).build_transaction(
            {
                "from": account.address,
                "value": execution_fee,
                "gas": 500000,
                "nonce": w3.eth.get_transaction_count(account.address),
                "maxFeePerGas": w3.eth.gas_price * 2,
                "maxPriorityFeePerGas": w3.to_wei(1, "gwei"),
            }
        )

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return {
            "position_id": position_id,
            "realized_pnl_usd": 0.0,  # actual PnL requires oracle query
            "tx_hash": tx_hash.hex(),
            "status": "success" if receipt.status == 1 else "failed",
            "block": receipt.blockNumber,
            "arbitrum_explorer": f"https://arbiscan.io/tx/{tx_hash.hex()}",
            "dry_run": False,
        }

    except Exception as exc:
        return {
            "error": str(exc),
            "position_id": position_id,
            "dry_run": False,
        }


# ── Tool 6: dca ────────────────────────────────────────────────────────────────


def _dca(args: dict) -> dict:
    token: str = args["token"]
    amount_usd: float = float(args["amount_usd"])
    frequency_hours: int = int(args.get("frequency_hours", 168))

    schedule_id = f"dca-{token.lower()}-{uuid.uuid4().hex[:8]}"
    now_ts = int(time.time())
    next_execution_ts = now_ts + frequency_hours * 3600
    next_execution = datetime.fromtimestamp(next_execution_ts, tz=timezone.utc).isoformat()

    # Try MoonPay CLI
    moonpay_result = run_moonpay_cli(
        [
            "dca",
            "--token",
            token,
            "--amount",
            str(amount_usd),
            "--frequency",
            f"{frequency_hours}h",
        ]
    )

    if not moonpay_result.get("demo"):
        # MoonPay CLI succeeded
        schedule = {
            "schedule_id": moonpay_result.get("schedule_id", schedule_id),
            "token": token,
            "amount_usd": amount_usd,
            "frequency_hours": frequency_hours,
            "next_execution": next_execution,
            "source": "moonpay_cli",
            "moonpay_data": moonpay_result,
        }
    else:
        # Local schedule — nexus-monitor will pick this up
        schedule = {
            "schedule_id": schedule_id,
            "token": token,
            "amount_usd": amount_usd,
            "frequency_hours": frequency_hours,
            "created_at": datetime.fromtimestamp(now_ts, tz=timezone.utc).isoformat(),
            "next_execution": next_execution,
            "active": True,
            "source": "local",
            "note": "Stored locally — nexus-monitor executes on schedule",
        }

    # Persist schedule
    schedules = _load_dca_schedules()
    schedules.append(schedule)
    _save_dca_schedules(schedules)

    return schedule


# ── Tool 7: bridge ────────────────────────────────────────────────────────────


def _bridge(args: dict) -> dict:
    token: str = args["token"]
    amount: float = float(args["amount"])
    from_chain: str = args["from_chain"]
    to_chain: str = args["to_chain"]

    # Bridge time estimates by chain pair
    time_estimates = {
        ("ethereum", "base"): 2,
        ("base", "ethereum"): 7,
        ("ethereum", "arbitrum"): 10,
        ("arbitrum", "ethereum"): 7,
        ("base", "arbitrum"): 15,
        ("arbitrum", "base"): 15,
    }
    estimated_minutes = time_estimates.get((from_chain, to_chain), 15)

    # Try MoonPay CLI
    moonpay_result = run_moonpay_cli(
        [
            "bridge",
            "--token",
            token,
            "--amount",
            str(amount),
            "--from",
            from_chain,
            "--to",
            to_chain,
        ]
    )

    if not moonpay_result.get("demo"):
        return {
            "tx_hash": moonpay_result.get("tx_hash"),
            "token": token,
            "amount": amount,
            "from_chain": from_chain,
            "to_chain": to_chain,
            "estimated_time_minutes": estimated_minutes,
            "source": "moonpay_cli",
            "moonpay_data": moonpay_result,
        }

    # Demo fallback
    demo_tx = f"0x{'0' * 40}{uuid.uuid4().hex[:24]}"
    return {
        "tx_hash": demo_tx,
        "token": token,
        "amount": amount,
        "from_chain": from_chain,
        "to_chain": to_chain,
        "estimated_time_minutes": estimated_minutes,
        "demo": True,
        "note": "Demo bridge — MoonPay CLI not installed. Install with: npm install -g @moonpay/cli",
    }


# ── Tool 8: get_portfolio ─────────────────────────────────────────────────────


async def _get_portfolio(args: dict) -> dict:
    address: str = args.get("address", "") or os.environ.get("WALLET_ADDRESS", "")

    if not address:
        return {"error": "No address provided and WALLET_ADDRESS env var not set"}

    rpc_urls = {
        "ethereum": os.environ.get("ETHEREUM_RPC_URL", "https://eth.llamarpc.com"),
        "base": os.environ.get("BASE_RPC_URL", "https://mainnet.base.org"),
        "arbitrum": os.environ.get("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
    }

    # ERC-20 balanceOf ABI
    erc20_abi = [
        {
            "name": "balanceOf",
            "type": "function",
            "inputs": [{"name": "account", "type": "address"}],
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
        }
    ]

    balances: dict[str, dict[str, float]] = {}
    total_value_usd = 0.0
    errors: list[str] = []

    for chain, rpc_url in rpc_urls.items():
        chain_balances: dict[str, float] = {}
        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
            checksum_addr = Web3.to_checksum_address(address)

            # Native ETH balance
            eth_wei = w3.eth.get_balance(checksum_addr)
            eth_balance = eth_wei / 10**18
            chain_balances["ETH"] = round(eth_balance, 6)
            total_value_usd += eth_balance * _DEMO_PRICES["ETH"]

            # USDC balance
            usdc_addr = TOKEN_ADDRESSES.get(chain, {}).get("USDC")
            if usdc_addr and usdc_addr != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                usdc_contract = w3.eth.contract(
                    address=Web3.to_checksum_address(usdc_addr), abi=erc20_abi
                )
                usdc_raw = usdc_contract.functions.balanceOf(checksum_addr).call()
                usdc_balance = usdc_raw / 10**6
                chain_balances["USDC"] = round(usdc_balance, 2)
                total_value_usd += usdc_balance * _DEMO_PRICES["USDC"]

            # ARB token on Arbitrum
            if chain == "arbitrum":
                arb_addr = TOKEN_ADDRESSES["arbitrum"].get("ARB")
                if arb_addr:
                    arb_contract = w3.eth.contract(
                        address=Web3.to_checksum_address(arb_addr), abi=erc20_abi
                    )
                    arb_raw = arb_contract.functions.balanceOf(checksum_addr).call()
                    arb_balance = arb_raw / 10**18
                    chain_balances["ARB"] = round(arb_balance, 4)
                    total_value_usd += arb_balance * _DEMO_PRICES["ARB"]

        except Exception as exc:
            errors.append(f"{chain}: {exc}")
            # Provide zero balances so the response is still useful
            chain_balances.setdefault("ETH", 0.0)
            chain_balances.setdefault("USDC", 0.0)

        balances[chain] = chain_balances

    result: dict[str, Any] = {
        "address": address,
        "total_value_usd": round(total_value_usd, 2),
        "balances": balances,
        "prices_used": _DEMO_PRICES,
    }
    if errors:
        result["rpc_errors"] = errors
        result["note"] = "Some chains unavailable — set RPC env vars for live data"

    return result


# ── Entry point ────────────────────────────────────────────────────────────────


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
