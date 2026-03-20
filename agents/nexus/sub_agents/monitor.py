"""
nexus-monitor — Lido vault monitor + Telegram alerter.

Strategy:
- Polls Lido stETH APY every 15 minutes (configurable)
- Sends Telegram alert if APY drops more than 10% relative to last reading
- Tracks vault health metrics

Env vars:
    TELEGRAM_BOT_TOKEN   — Telegram bot token for alerts
    TELEGRAM_CHAT_ID     — Telegram chat/channel ID to send alerts to
    MONITOR_INTERVAL_SECS — Poll interval in seconds (default: 900)
"""
from __future__ import annotations

import os
from typing import Any

import httpx

from agents.nexus.sub_agents.base import SubAgent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LIDO_APR_URL = "https://eth-api.lido.fi/v1/protocol/steth/apr/last"
APY_DROP_ALERT_THRESHOLD_PCT = 10.0  # alert if APY drops > 10% relative


class NexusMonitor(SubAgent):
    """
    Lido vault health monitor with Telegram alerting.
    """

    agent_id = "nexus-monitor"
    description = "Lido vault monitor with Telegram APY drop alerts"

    def __init__(self) -> None:
        super().__init__()
        self.telegram_token: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat: str = os.environ.get("TELEGRAM_CHAT_ID", "")
        self.poll_interval: int = int(
            os.environ.get("MONITOR_INTERVAL_SECS", "900")
        )
        self._last_apy: float = 0.0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run_cycle(self) -> dict[str, Any]:
        """
        Monitoring cycle:
        1. Fetch stETH APY from Lido
        2. Compare to last reading; alert via Telegram if drop > 10%
        3. Log vault health
        """
        result = await self.get_vault_health()
        self.log_action("vault_health_check", result)
        return result

    async def get_vault_health(self) -> dict[str, Any]:
        """
        Fetch Lido stETH APY and compute health metrics.

        Returns vault health dict including apy, drop_pct, alert flag.
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(LIDO_APR_URL)
                if r.status_code != 200:
                    return {"error": f"HTTP {r.status_code}", "status": "error"}

                apy = float(r.json().get("data", {}).get("apr", 4.0))
                drop_pct = (
                    (self._last_apy - apy) / self._last_apy * 100
                    if self._last_apy > 0
                    else 0.0
                )
                alert = drop_pct > APY_DROP_ALERT_THRESHOLD_PCT

                if alert and self.telegram_token:
                    await self._send_telegram(
                        f"⚠️ Nexus Monitor: stETH APY dropped {drop_pct:.1f}% → {apy:.2f}%"
                    )

                self._last_apy = apy
                return {
                    "apy": apy,
                    "drop_pct": round(drop_pct, 2),
                    "alert": alert,
                    "status": "ok",
                }

        except Exception as exc:
            return {"error": str(exc), "status": "error"}

    async def _send_telegram(self, msg: str) -> None:
        """Send a message via Telegram Bot API. Silently fails on error."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(
                    f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                    json={"chat_id": self.telegram_chat, "text": msg},
                )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Status extension
    # ------------------------------------------------------------------

    async def get_status(self) -> dict[str, Any]:
        base = await super().get_status()
        base["last_apy"] = self._last_apy
        base["poll_interval_secs"] = self.poll_interval
        base["telegram_configured"] = bool(self.telegram_token and self.telegram_chat)
        return base
