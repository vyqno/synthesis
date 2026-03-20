"""
nexus-scorer — Olas mech-server + public goods evaluator.

Strategy:
- Serves evaluation requests via Olas mech protocol
- Uses Venice AI (LLM) to score project impact and legitimacy
- Returns structured JSON: {impact, legitimacy, recommendation, red_flags}

Env vars:
    VENICE_API_KEY       — Venice AI API key for LLM inference
    VENICE_MODEL         — Model to use (default: llama-3.3-70b)
    OLAS_MECH_KEY        — Olas mech registration key
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

from agents.nexus.sub_agents.base import SubAgent


class NexusScorer(SubAgent):
    """
    Public goods evaluator: scores projects via Venice AI LLM + Olas mech protocol.
    """

    agent_id = "nexus-scorer"
    description = "Olas mech-server + public goods impact scorer"

    def __init__(self) -> None:
        super().__init__()
        self.venice_api_key: str = os.environ.get("VENICE_API_KEY", "")
        self.venice_model: str = os.environ.get("VENICE_MODEL", "llama-3.3-70b")
        self.olas_mech_key: str = os.environ.get("OLAS_MECH_KEY", "")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run_cycle(self) -> dict[str, Any]:
        """
        Scorer is request-driven, not polling.
        Cycle returns readiness status only.
        """
        result = {
            "status": "waiting_for_requests",
            "olas_registered": bool(self.olas_mech_key),
            "venice_configured": bool(self.venice_api_key),
            "model": self.venice_model,
        }
        self.log_action("heartbeat", result)
        return result

    async def evaluate_project(self, project_url: str) -> dict[str, Any]:
        """
        Evaluate a project URL for public goods impact and legitimacy.

        Returns:
            {impact: 0-100, legitimacy: 0-100, recommendation: str, red_flags: list}
        """
        prompt = (
            f"Evaluate this project for public goods impact and legitimacy: {project_url}\n"
            "Return JSON with keys: impact (0-100), legitimacy (0-100), "
            "recommendation (string), red_flags (list of strings)."
        )
        result: dict[str, Any] = {
            "impact": 50,
            "legitimacy": 50,
            "recommendation": "Needs more data",
            "red_flags": [],
            "project_url": project_url,
        }

        if not self.venice_api_key:
            result["note"] = "VENICE_API_KEY not configured — returning defaults"
            return result

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    "https://api.venice.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.venice_api_key}"},
                    json={
                        "model": self.venice_model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"]
                    m = re.search(r"\{.*\}", content, re.DOTALL)
                    if m:
                        parsed = json.loads(m.group())
                        result.update(parsed)
        except Exception:
            pass

        return result

    async def serve_olas_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle an incoming Olas mech evaluation request."""
        project_url = request.get("project_url", request.get("task", ""))
        result = await self.evaluate_project(project_url)
        self.log_action("olas_evaluation", {"request": request, "result": result})
        return result
