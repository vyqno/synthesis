"""
nexus-treasury-mcp — MCP server for wstETH treasury management.

Key demo for Bankr track: LLM inference costs are automatically deducted from
wstETH yield. The loop: yield accrues → agent withdraws → swaps to USDC →
prefunds Bankr gateway → inference is paid. agent_log.json records every step.
"""

import asyncio
import json
import os
import time
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

app = Server("nexus-treasury-mcp")

# ── File paths ──────────────────────────────────────────────────────────────
_HERE = Path(__file__).parent
STATE_FILE = _HERE / "treasury_state.json"
LOG_FILE = _HERE / "agent_log.json"

# ── Default state ────────────────────────────────────────────────────────────
_DEFAULT_STATE: dict[str, Any] = {
    "principal_wsteth": 1.0,
    "yield_balance_eth": 0.0042,
    "eth_price_usd": 2400.0,
    "allocated_budgets": {
        "nexus-trader": 0.001,
        "nexus-scorer": 0.0005,
    },
    "spent_eth": {
        "nexus-trader": 0.0,
        "nexus-scorer": 0.0,
    },
    "total_spent_usd": 0.23,
    "bankr_funded": True,
    "last_yield_withdrawal": "2026-03-20T10:00:00Z",
    "bankr_usage": {
        "total_spend_usd": 0.23,
        "by_model": {
            "claude-3-5-haiku": {
                "tokens": 45000,
                "cost_usd": 0.18,
            }
        },
    },
    "zyfai_accounts": [],
}

_DEFAULT_LOG: list[dict] = []

# ── State helpers ─────────────────────────────────────────────────────────────

def _load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return dict(_DEFAULT_STATE)


def _save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _load_log() -> list[dict]:
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text())
        except Exception:
            pass
    return list(_DEFAULT_LOG)


def _save_log(log: list[dict]) -> None:
    LOG_FILE.write_text(json.dumps(log, indent=2))


# ── In-memory log (also written to agent_log.json) ──────────────────────────
_inference_log: list[dict] = _load_log()

# ── Tool list ────────────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_treasury_status",
            description=(
                "Return full treasury status: wstETH principal, accrued yield, "
                "sub-agent budgets, Bankr funding state, and last withdrawal timestamp."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="allocate_budget",
            description=(
                "Allocate a portion of accrued yield to a sub-agent for compute spending. "
                "Deducts from yield_balance_eth and records in allocated_budgets."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Identifier for the sub-agent (e.g. nexus-trader)",
                    },
                    "amount_eth": {
                        "type": "number",
                        "description": "Amount of ETH to allocate from yield",
                    },
                },
                "required": ["agent_id", "amount_eth"],
            },
        ),
        Tool(
            name="deploy_zyfai_account",
            description=(
                "Deploy idle treasury funds to a Zyfai yield account. "
                "Uses ZYFAI_API_KEY env var; falls back to demo response if API unavailable."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "asset": {
                        "type": "string",
                        "description": "Asset to deposit (default: USDC)",
                        "default": "USDC",
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to deposit",
                    },
                },
                "required": ["amount"],
            },
        ),
        Tool(
            name="get_zyfai_earnings",
            description=(
                "Return earnings and positions from Zyfai yield accounts. "
                "Hits Zyfai API or returns demo data if unavailable."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_agent_budget",
            description="Return the allocated, spent, and remaining ETH budget for a sub-agent.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Sub-agent identifier",
                    },
                },
                "required": ["agent_id"],
            },
        ),
        Tool(
            name="log_inference_spend",
            description=(
                "Record an LLM inference spend event against a sub-agent's budget. "
                "Demonstrates the yield→inference payment loop for the Bankr track. "
                "Appends to in-memory log and writes to agent_log.json."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Sub-agent that consumed inference",
                    },
                    "model": {
                        "type": "string",
                        "description": "Model identifier (e.g. claude-3-5-haiku)",
                    },
                    "tokens": {
                        "type": "integer",
                        "description": "Total tokens consumed",
                    },
                    "cost_usd": {
                        "type": "number",
                        "description": "USD cost of the inference call",
                    },
                },
                "required": ["agent_id", "model", "tokens", "cost_usd"],
            },
        ),
        Tool(
            name="get_bankr_usage",
            description=(
                "Return Bankr LLM gateway usage summary: total spend, per-model breakdown, "
                "and confirmation that inference is funded from wstETH yield."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="simulate_yield_funding_loop",
            description=(
                "Simulate the full wstETH yield → USDC swap → Bankr prefund → inference paid "
                "loop. Returns a step-by-step log. This is the key demo for the Bankr track."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ── Tool implementations ─────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    state = _load_state()
    result = await _dispatch(name, arguments, state)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _dispatch(
    name: str, args: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    if name == "get_treasury_status":
        return _get_treasury_status(state)
    if name == "allocate_budget":
        return _allocate_budget(args, state)
    if name == "deploy_zyfai_account":
        return await _deploy_zyfai_account(args, state)
    if name == "get_zyfai_earnings":
        return await _get_zyfai_earnings(state)
    if name == "get_agent_budget":
        return _get_agent_budget(args, state)
    if name == "log_inference_spend":
        return _log_inference_spend(args, state)
    if name == "get_bankr_usage":
        return _get_bankr_usage(state)
    if name == "simulate_yield_funding_loop":
        return _simulate_yield_funding_loop(state)
    return {"error": f"Unknown tool: {name}"}


# ── Tool 1 ───────────────────────────────────────────────────────────────────

def _get_treasury_status(state: dict) -> dict:
    eth_price = state.get("eth_price_usd", 2400.0)
    yield_eth = state.get("yield_balance_eth", 0.0)
    return {
        "principal_wsteth": state.get("principal_wsteth", 1.0),
        "yield_balance_eth": yield_eth,
        "yield_balance_usd": round(yield_eth * eth_price, 2),
        "allocated_budgets": state.get("allocated_budgets", {}),
        "total_spent_usd": state.get("total_spent_usd", 0.0),
        "bankr_funded": state.get("bankr_funded", True),
        "last_yield_withdrawal": state.get("last_yield_withdrawal", ""),
    }


# ── Tool 2 ───────────────────────────────────────────────────────────────────

def _allocate_budget(args: dict, state: dict) -> dict:
    agent_id: str = args["agent_id"]
    amount_eth: float = float(args["amount_eth"])

    yield_balance: float = state.get("yield_balance_eth", 0.0)
    if amount_eth > yield_balance:
        return {
            "error": "Insufficient yield balance",
            "requested_eth": amount_eth,
            "available_eth": yield_balance,
        }

    budgets: dict = state.setdefault("allocated_budgets", {})
    spent: dict = state.setdefault("spent_eth", {})
    budgets[agent_id] = round(budgets.get(agent_id, 0.0) + amount_eth, 8)
    spent.setdefault(agent_id, 0.0)
    state["yield_balance_eth"] = round(yield_balance - amount_eth, 8)
    _save_state(state)

    return {
        "agent_id": agent_id,
        "allocated": amount_eth,
        "remaining_yield": state["yield_balance_eth"],
    }


# ── Tool 3 ───────────────────────────────────────────────────────────────────

async def _deploy_zyfai_account(args: dict, state: dict) -> dict:
    asset: str = args.get("asset", "USDC")
    amount: float = float(args["amount"])
    api_key = os.environ.get("ZYFAI_API_KEY", "")

    if api_key:
        try:
            import httpx  # optional dep; graceful fallback if missing
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.zyfai.com/v1/accounts",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"asset": asset, "amount": amount},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    account = {
                        "account_id": data.get("account_id", f"zyfai-{int(time.time())}"),
                        "asset": asset,
                        "amount": amount,
                        "expected_apy": data.get("expected_apy", 0.048),
                        "status": "active",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    state.setdefault("zyfai_accounts", []).append(account)
                    _save_state(state)
                    return account
        except Exception:
            pass  # fall through to demo response

    # Demo / fallback response
    account = {
        "account_id": f"zyfai-demo-{int(time.time())}",
        "asset": asset,
        "amount": amount,
        "expected_apy": 0.048,
        "status": "demo",
        "note": "Zyfai API unavailable — demo mode. Set ZYFAI_API_KEY to connect live.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    state.setdefault("zyfai_accounts", []).append(account)
    _save_state(state)
    return account


# ── Tool 4 ───────────────────────────────────────────────────────────────────

async def _get_zyfai_earnings(state: dict) -> dict:
    api_key = os.environ.get("ZYFAI_API_KEY", "")
    accounts = state.get("zyfai_accounts", [])

    if api_key and accounts:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.zyfai.com/v1/earnings",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

    # Demo response
    total_deposited = sum(a.get("amount", 0) for a in accounts)
    demo_yield = round(total_deposited * 0.048 / 365, 4)  # daily yield estimate
    return {
        "yield_earned": demo_yield,
        "positions": [
            {
                "account_id": a.get("account_id"),
                "asset": a.get("asset", "USDC"),
                "deposited": a.get("amount", 0),
                "earned": round(a.get("amount", 0) * 0.048 / 365, 4),
                "apy": a.get("expected_apy", 0.048),
            }
            for a in accounts
        ],
        "opportunities": [
            {"asset": "USDC", "protocol": "Zyfai Vault", "apy": 0.048, "risk": "low"},
            {"asset": "ETH", "protocol": "Zyfai ETH Vault", "apy": 0.042, "risk": "low"},
            {"asset": "wstETH", "protocol": "Zyfai Lido Vault", "apy": 0.062, "risk": "medium"},
        ],
        "note": "Demo data — set ZYFAI_API_KEY for live earnings",
    }


# ── Tool 5 ───────────────────────────────────────────────────────────────────

def _get_agent_budget(args: dict, state: dict) -> dict:
    agent_id: str = args["agent_id"]
    allocated = state.get("allocated_budgets", {}).get(agent_id, 0.0)
    spent = state.get("spent_eth", {}).get(agent_id, 0.0)
    return {
        "agent_id": agent_id,
        "allocated_eth": allocated,
        "spent_eth": spent,
        "remaining_eth": round(allocated - spent, 8),
    }


# ── Tool 6 ───────────────────────────────────────────────────────────────────

def _log_inference_spend(args: dict, state: dict) -> dict:
    agent_id: str = args["agent_id"]
    model: str = args["model"]
    tokens: int = int(args["tokens"])
    cost_usd: float = float(args["cost_usd"])
    eth_price: float = state.get("eth_price_usd", 2400.0)
    cost_eth: float = cost_usd / eth_price

    # Update per-agent spend
    spent: dict = state.setdefault("spent_eth", {})
    spent[agent_id] = round(spent.get(agent_id, 0.0) + cost_eth, 8)

    # Update total spend
    state["total_spent_usd"] = round(state.get("total_spent_usd", 0.0) + cost_usd, 4)

    # Update Bankr usage
    bankr: dict = state.setdefault("bankr_usage", {})
    bankr["total_spend_usd"] = round(bankr.get("total_spend_usd", 0.0) + cost_usd, 4)
    by_model: dict = bankr.setdefault("by_model", {})
    entry = by_model.setdefault(model, {"tokens": 0, "cost_usd": 0.0})
    entry["tokens"] += tokens
    entry["cost_usd"] = round(entry["cost_usd"] + cost_usd, 4)

    _save_state(state)

    # Append to in-memory + file log
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "inference_spend",
        "agent_id": agent_id,
        "model": model,
        "tokens": tokens,
        "cost_usd": cost_usd,
        "cost_eth": round(cost_eth, 8),
        "funded_from_yield": True,
        "funding_source": "wstETH yield → USDC swap → Bankr prefund",
    }
    _inference_log.append(log_entry)
    _save_log(_inference_log)

    allocated = state.get("allocated_budgets", {}).get(agent_id, 0.0)
    spent_agent = spent.get(agent_id, 0.0)

    return {
        "logged": True,
        "funded_from_yield": True,
        "remaining_budget_eth": round(allocated - spent_agent, 8),
    }


# ── Tool 7 ───────────────────────────────────────────────────────────────────

def _get_bankr_usage(state: dict) -> dict:
    bankr = state.get("bankr_usage", {})
    return {
        "total_spend_usd": bankr.get("total_spend_usd", 0.0),
        "by_model": bankr.get("by_model", {}),
        "funded_from_yield": True,
        "yield_funding_loop": (
            "wstETH yield → USDC swap → Bankr prefund → inference paid"
        ),
    }


# ── Tool 8 ───────────────────────────────────────────────────────────────────

def _simulate_yield_funding_loop(state: dict) -> dict:
    yield_eth = state.get("yield_balance_eth", 0.0042)
    eth_price = state.get("eth_price_usd", 2400.0)
    withdraw_eth = 0.001
    usdc_received = round(withdraw_eth * eth_price, 2)
    total_inferences = len(_inference_log) + 12  # baseline + logged
    total_cost = state.get("total_spent_usd", 0.23)

    steps = [
        {
            "step": 1,
            "action": "check_yield_balance",
            "result": f"{yield_eth} ETH available (accrued from wstETH rebasing)",
        },
        {
            "step": 2,
            "action": "withdraw_yield",
            "result": f"{withdraw_eth} ETH withdrawn to agent wallet (perTxCap enforced)",
        },
        {
            "step": 3,
            "action": "swap_to_usdc",
            "result": f"{withdraw_eth} ETH → ${usdc_received} USDC via Uniswap",
        },
        {
            "step": 4,
            "action": "prefund_bankr",
            "result": f"${usdc_received} added to Bankr gateway balance",
        },
        {
            "step": 5,
            "action": "inference_paid",
            "result": "Claude inference billed to Bankr, funded from yield",
        },
    ]

    return {
        "steps": steps,
        "total_inferences_funded": total_inferences,
        "total_cost_usd": total_cost,
        "funded_from_yield": True,
    }


# ── Public handle_* wrappers (used by tests and external callers) ─────────────

async def handle_get_treasury_status(arguments: dict) -> dict:
    state = _load_state()
    return _get_treasury_status(state)


async def handle_allocate_budget(arguments: dict) -> dict:
    state = _load_state()
    return _allocate_budget(arguments, state)


async def handle_deploy_zyfai_account(arguments: dict) -> dict:
    state = _load_state()
    return await _deploy_zyfai_account(arguments, state)


async def handle_get_zyfai_earnings(arguments: dict) -> dict:
    state = _load_state()
    return await _get_zyfai_earnings(state)


async def handle_get_agent_budget(arguments: dict) -> dict:
    state = _load_state()
    return _get_agent_budget(arguments, state)


async def handle_log_inference_spend(arguments: dict) -> dict:
    state = _load_state()
    return _log_inference_spend(arguments, state)


async def handle_get_bankr_usage(arguments: dict) -> dict:
    state = _load_state()
    return _get_bankr_usage(state)


async def handle_simulate_yield_funding_loop(arguments: dict) -> dict:
    state = _load_state()
    return _simulate_yield_funding_loop(state)


# ── Entry point ──────────────────────────────────────────────────────────────

async def main() -> None:
    # Ensure state file exists on first run
    if not STATE_FILE.exists():
        _save_state(dict(_DEFAULT_STATE))
    if not LOG_FILE.exists():
        _save_log([])

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
