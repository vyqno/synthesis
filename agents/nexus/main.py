"""
Nexus Main — autonomous agent loop.
Runs continuously: check yield → allocate budgets → dispatch tasks → log results.
"""
from __future__ import annotations

import asyncio
import os
import threading
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from agents.nexus.brain import NexusBrain, log_action
from agents.nexus.treasury import NexusTreasury


async def autonomous_loop(brain: NexusBrain, treasury: NexusTreasury) -> None:
    """Main decision loop: runs every 5 minutes."""
    log_action("startup", "Nexus agent starting autonomous loop")

    while True:
        try:
            # 1. Check yield balance
            status = treasury.get_treasury_status()
            log_action("check_yield_balance", f"{status['yield_balance_eth']:.6f} ETH available")

            # 2. If yield available, make allocation decisions
            if status["available_eth"] > 0.0001:
                decision = brain.decide(
                    f"Treasury has {status['available_eth']:.6f} ETH yield available. "
                    "Which sub-agents should receive budget allocations? "
                    "Consider: nexus-trader for DeFi ops, nexus-scorer for public goods evaluation. "
                    "Suggest allocations as JSON: {agent_id: amount_eth}",
                    context=status,
                    private=True,
                )
                log_action("allocation_decision", decision[:200])

            # 3. Wait 5 minutes
            await asyncio.sleep(300)

        except KeyboardInterrupt:
            log_action("shutdown", "Nexus agent stopping")
            break
        except Exception as e:
            log_action("error", str(e))
            await asyncio.sleep(60)


def main() -> None:
    import threading
    from scripts.health_server import start_health_server
    threading.Thread(target=start_health_server, daemon=True).start()

    from agents.nexus.wallet import get_wallet_status, check_policy
    wallet_status = get_wallet_status()
    log_action("wallet_init", wallet_status)

    brain = NexusBrain()
    treasury = NexusTreasury()

    log_action("init", {
        "agent": "nexus",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "bankr_configured": bool(os.getenv("BANKR_API_KEY")),
        "venice_configured": bool(os.getenv("VENICE_API_KEY")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
    })

    asyncio.run(autonomous_loop(brain, treasury))


if __name__ == "__main__":
    main()
