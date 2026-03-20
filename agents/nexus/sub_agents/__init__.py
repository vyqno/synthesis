"""
Nexus Sub-Agents — modular autonomous agent components.

Each sub-agent has its own decision loop, budget allocation, and Olas integration.
"""
from __future__ import annotations

from agents.nexus.sub_agents.base import SubAgent
from agents.nexus.sub_agents.trader import NexusTrader
from agents.nexus.sub_agents.staker import NexusStaker
from agents.nexus.sub_agents.scorer import NexusScorer
from agents.nexus.sub_agents.keeper import NexusKeeper
from agents.nexus.sub_agents.prover import NexusProver
from agents.nexus.sub_agents.monitor import NexusMonitor

ALL_AGENTS: list[type[SubAgent]] = [
    NexusTrader,
    NexusStaker,
    NexusScorer,
    NexusKeeper,
    NexusProver,
    NexusMonitor,
]

__all__ = [
    "SubAgent",
    "NexusTrader",
    "NexusStaker",
    "NexusScorer",
    "NexusKeeper",
    "NexusProver",
    "NexusMonitor",
    "ALL_AGENTS",
]
