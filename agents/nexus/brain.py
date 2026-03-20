"""
Nexus Brain — LLM orchestrator with multi-model fallback.

Primary: Bankr LLM Gateway (https://docs.bankr.bot/llm-gateway/overview)
Fallback 1: Venice API (OpenAI-compatible, no data retention)
Fallback 2: Groq qwen/qwen3-32b
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

LOG_FILE = Path(__file__).parent.parent.parent / "agent_log.json"


def _load_log() -> dict:
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return {"agent": "nexus", "session": datetime.now(timezone.utc).isoformat(), "entries": []}


def _save_log(log: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(log, indent=2))


def log_action(action: str, result: Any, tool: str = "", params: dict | None = None, tx_hash: str = "") -> None:
    """Append an action to agent_log.json."""
    log = _load_log()
    entry: dict[str, Any] = {
        "t": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "agent": "nexus",
        "action": action,
        "result": result,
    }
    if tool:
        entry["tool"] = tool
    if params:
        entry["params"] = params
    if tx_hash:
        entry["tx_hash"] = tx_hash
    log["entries"].append(entry)
    _save_log(log)


class NexusBrain:
    """
    LLM orchestrator. Tries Bankr → Venice → Groq in order.
    Tracks spend for treasury accounting.
    """

    BANKR_BASE = "https://api.bankr.bot/v1"  # Bankr LLM Gateway
    VENICE_BASE = "https://api.venice.ai/api/v1"
    GROQ_BASE = "https://api.groq.com/openai/v1"

    def __init__(self) -> None:
        self.bankr_key = os.getenv("BANKR_API_KEY", "")
        self.venice_key = os.getenv("VENICE_API_KEY", "")
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.total_spend_usd = 0.0

    def _chat(self, base_url: str, api_key: str, model: str, messages: list[dict], **kwargs) -> str:
        """Raw OpenAI-compatible chat completion call."""
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": model, "messages": messages, **kwargs},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def decide(self, task: str, context: dict | None = None, private: bool = False) -> str:
        """
        Make a decision or generate a response for a given task.

        Args:
            task: The task description or question
            context: Additional context dict
            private: If True, use Venice (no data retention) for sensitive reasoning
        Returns:
            LLM response string
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Nexus, an autonomous AI agent. You manage a DeFi treasury, "
                    "coordinate sub-agents, and make decisions to maximize value for the network. "
                    "Be concise and action-oriented."
                ),
            }
        ]
        if context:
            messages.append({"role": "user", "content": f"Context: {json.dumps(context)}"})
        messages.append({"role": "user", "content": task})

        # Private reasoning always goes through Venice
        if private and self.venice_key:
            try:
                result = self._chat(self.VENICE_BASE, self.venice_key, "venice-uncensored", messages)
                log_action("decide", {"model": "venice", "task": task[:100]})
                return result
            except Exception as e:
                log_action("decide_fallback", {"error": str(e), "from": "venice"})

        # Try Bankr first (multi-model gateway, pays from yield)
        if self.bankr_key:
            try:
                result = self._chat(self.BANKR_BASE, self.bankr_key, "claude-3-5-haiku-20241022", messages)
                log_action("decide", {"model": "bankr/claude", "task": task[:100]})
                return result
            except Exception as e:
                log_action("decide_fallback", {"error": str(e), "from": "bankr"})

        # Fallback to Venice
        if self.venice_key:
            try:
                result = self._chat(self.VENICE_BASE, self.venice_key, "venice-uncensored", messages)
                log_action("decide", {"model": "venice", "task": task[:100]})
                return result
            except Exception as e:
                log_action("decide_fallback", {"error": str(e), "from": "venice"})

        # Final fallback: Groq
        if self.groq_key:
            result = self._chat(self.GROQ_BASE, self.groq_key, "qwen/qwen3-32b", messages)
            log_action("decide", {"model": "groq/qwen3-32b", "task": task[:100]})
            return result

        raise RuntimeError("No LLM backend available — set BANKR_API_KEY, VENICE_API_KEY, or GROQ_API_KEY")

    def get_compute_budget(self) -> float:
        """Returns available compute budget in ETH (reads from treasury module)."""
        try:
            from agents.nexus.treasury import NexusTreasury
            t = NexusTreasury()
            return t.get_yield_balance()
        except Exception:
            return 0.0

    def route_task(self, task: str) -> str:
        """
        Decide which sub-agent should handle a task.
        Returns: agent name (nexus-trader, nexus-staker, nexus-scorer, etc.)
        """
        routing_prompt = f"""Given this task, which sub-agent should handle it?
Task: {task}

Sub-agents:
- nexus-trader: Uniswap swaps, GMX positions, token operations
- nexus-staker: Lido staking, wstETH operations, yield management
- nexus-scorer: Public goods evaluation, Octant scoring
- nexus-keeper: Filecoin storage, state persistence
- nexus-prover: Noir ZK proof generation and verification
- nexus-monitor: Vault monitoring, alerts

Reply with ONLY the sub-agent name, nothing else."""
        return self.decide(routing_prompt).strip().lower()
