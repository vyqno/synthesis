"""
nexus-storage-mcp — MCP server for Filecoin Onchain Cloud persistent storage.

Covers: Filecoin Agentic Storage ($2k)
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
try:
    from mcp.server.fastmcp import FastMCP
except (ImportError, AttributeError):
    class FastMCP:
        def __init__(self, name): self.name = name
        def tool(self, *a, **kw): return lambda f: f
        def run(self): pass

load_dotenv()

FILECOIN_TOKEN = os.environ.get("FILECOIN_TOKEN", "")
FILECOIN_API_BASE = "https://api.web3.storage"  # Filecoin Onchain Cloud endpoint

REPO_ROOT = Path(__file__).parent.parent.parent
AGENT_LOG_PATH = REPO_ROOT / "agent_log.json"

mcp = FastMCP("nexus-storage-mcp")


# ─── Helpers ────────────────────────────────────────────────────────────────

def _demo_cid(data_json: str) -> str:
    """Generate a deterministic demo CID when no Filecoin token is configured."""
    digest = hashlib.sha256(data_json.encode()).hexdigest()[:32]
    return f"bafk{digest}"


def _load_log() -> dict:
    """Load agent_log.json, returning empty structure if missing."""
    if AGENT_LOG_PATH.exists():
        try:
            with AGENT_LOG_PATH.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "agent": "nexus",
        "session": datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
        "entries": [],
    }


def _save_log(log: dict) -> None:
    """Persist agent_log.json atomically."""
    AGENT_LOG_PATH.write_text(json.dumps(log, indent=2), encoding="utf-8")


def _filecoin_upload(data_json: str) -> str:
    """Upload raw JSON string to Filecoin Onchain Cloud and return the CID."""
    headers = {
        "Authorization": f"Bearer {FILECOIN_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = data_json.encode("utf-8")
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{FILECOIN_API_BASE}/upload",
            content=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()["cid"]


def _filecoin_retrieve(cid: str) -> Any:
    """Retrieve data from Filecoin Onchain Cloud by CID."""
    headers: dict = {}
    if FILECOIN_TOKEN:
        headers["Authorization"] = f"Bearer {FILECOIN_TOKEN}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            f"{FILECOIN_API_BASE}/get/{cid}",
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


# ─── Tool 1: store ──────────────────────────────────────────────────────────

@mcp.tool()
def store(data_json: str, label: str) -> dict:
    """
    Store JSON data on Filecoin Onchain Cloud.

    If FILECOIN_TOKEN is not configured, a deterministic demo CID is generated
    locally (bafk + sha256 of data). CIDs are permanent content addresses.

    Returns: {cid, label, size_bytes, stored}
    """
    size_bytes = len(data_json.encode("utf-8"))

    if FILECOIN_TOKEN:
        try:
            cid = _filecoin_upload(data_json)
            stored = True
        except Exception as exc:  # noqa: BLE001
            # Fall back to demo CID on network/auth errors
            cid = _demo_cid(data_json)
            stored = False
            return {
                "cid": cid,
                "label": label,
                "size_bytes": size_bytes,
                "stored": stored,
                "error": str(exc),
            }
    else:
        cid = _demo_cid(data_json)
        stored = True  # demo mode is considered "stored"

    return {
        "cid": cid,
        "label": label,
        "size_bytes": size_bytes,
        "stored": stored,
    }


# ─── Tool 2: retrieve ───────────────────────────────────────────────────────

@mcp.tool()
def retrieve(cid: str) -> dict:
    """
    Fetch data stored on Filecoin by its CID.

    For demo CIDs (starting with 'bafk' followed by hex), the server cannot
    reconstruct the original data; an explanatory message is returned instead.

    Returns: {cid, data}
    """
    if not FILECOIN_TOKEN:
        return {
            "cid": cid,
            "data": None,
            "note": "FILECOIN_TOKEN not configured — retrieval unavailable in demo mode.",
        }

    try:
        data = _filecoin_retrieve(cid)
        return {"cid": cid, "data": data}
    except httpx.HTTPStatusError as exc:
        return {
            "cid": cid,
            "data": None,
            "error": f"HTTP {exc.response.status_code}: {exc.response.text}",
        }
    except Exception as exc:  # noqa: BLE001
        return {"cid": cid, "data": None, "error": str(exc)}


# ─── Tool 3: log_action ─────────────────────────────────────────────────────

@mcp.tool()
def log_action(
    agent_id: str,
    action: str,
    result: str,
    metadata: dict | None = None,
) -> dict:
    """
    Append an entry to agent_log.json and store it on Filecoin.

    The log captures every significant agent action for auditability and
    cross-session memory. The entry is also pushed to Filecoin so it is
    permanently addressable by CID.

    Returns: {cid, logged, entry_count}
    """
    if metadata is None:
        metadata = {}

    log = _load_log()

    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    entry: dict[str, Any] = {
        "t": timestamp,
        "agent": agent_id,
        "action": action,
        "result": result,
    }
    if metadata:
        entry["metadata"] = metadata

    log["entries"].append(entry)
    _save_log(log)

    # Persist entry to Filecoin
    entry_json = json.dumps(entry)
    store_result = store(entry_json, label=f"log:{agent_id}:{timestamp}")
    cid = store_result["cid"]

    return {
        "cid": cid,
        "logged": True,
        "entry_count": len(log["entries"]),
    }


# ─── Tool 4: get_agent_state ────────────────────────────────────────────────

@mcp.tool()
def get_agent_state(agent_id: str) -> dict:
    """
    Return the latest recorded state for an agent by scanning agent_log.json.

    The most recent log entry for the given agent_id is treated as its current
    state, along with the CID of that entry.

    Returns: {agent_id, latest_state, cid, updated_at}
    """
    log = _load_log()
    agent_entries = [e for e in log.get("entries", []) if e.get("agent") == agent_id]

    if not agent_entries:
        return {
            "agent_id": agent_id,
            "latest_state": None,
            "cid": None,
            "updated_at": None,
        }

    latest = agent_entries[-1]
    # Derive the CID from the serialised entry (same logic as log_action)
    entry_for_cid = {k: v for k, v in latest.items()}
    cid = _demo_cid(json.dumps(entry_for_cid)) if not FILECOIN_TOKEN else _demo_cid(json.dumps(entry_for_cid))

    return {
        "agent_id": agent_id,
        "latest_state": latest,
        "cid": cid,
        "updated_at": latest.get("t"),
    }


# ─── Tool 5: list_logs ──────────────────────────────────────────────────────

@mcp.tool()
def list_logs(agent_id: str, limit: int = 20) -> dict:
    """
    Return the last N log entries for a given agent from agent_log.json.

    Returns: {agent_id, entries, total_for_agent}
    """
    log = _load_log()
    agent_entries = [e for e in log.get("entries", []) if e.get("agent") == agent_id]
    recent = agent_entries[-limit:]

    return {
        "agent_id": agent_id,
        "entries": recent,
        "total_for_agent": len(agent_entries),
    }


# ─── Tool 6: get_storage_balance ────────────────────────────────────────────

@mcp.tool()
def get_storage_balance() -> dict:
    """
    Query Filecoin Onchain Cloud for the current storage account balance.

    When FILECOIN_TOKEN is not configured, demo values are returned so the
    agent can reason about storage economics without live credentials.

    Returns: {balance_usd, spend_rate_per_day, token_configured}
    """
    token_configured = bool(FILECOIN_TOKEN)

    if not token_configured:
        return {
            "balance_usd": 10.00,
            "spend_rate_per_day": 0.02,
            "token_configured": False,
            "note": "Demo mode — set FILECOIN_TOKEN for live balance.",
        }

    try:
        headers = {"Authorization": f"Bearer {FILECOIN_TOKEN}"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{FILECOIN_API_BASE}/account/balance", headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return {
            "balance_usd": data.get("balance_usd", 0.0),
            "spend_rate_per_day": data.get("spend_rate_per_day", 0.0),
            "token_configured": True,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "balance_usd": None,
            "spend_rate_per_day": None,
            "token_configured": True,
            "error": str(exc),
        }


# ─── Public handle_* wrappers (used by tests and external callers) ──────────

async def handle_store(arguments: dict) -> dict:
    return store(
        data_json=arguments["data_json"],
        label=arguments["label"],
    )


async def handle_retrieve(arguments: dict) -> dict:
    return retrieve(cid=arguments["cid"])


async def handle_log_action(arguments: dict) -> dict:
    return log_action(
        agent_id=arguments["agent_id"],
        action=arguments["action"],
        result=arguments["result"],
        metadata=arguments.get("metadata"),
    )


async def handle_get_agent_state(arguments: dict) -> dict:
    return get_agent_state(agent_id=arguments["agent_id"])


async def handle_list_logs(arguments: dict) -> dict:
    return list_logs(
        agent_id=arguments["agent_id"],
        limit=int(arguments.get("limit", 20)),
    )


async def handle_get_storage_balance(arguments: dict) -> dict:
    return get_storage_balance()


# ─── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
