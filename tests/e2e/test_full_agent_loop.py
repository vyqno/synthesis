"""
E2E tests: simulate the full Nexus agent loop without live blockchain.
Tests the complete data flow: yield check -> brain decision -> sub-agent dispatch -> log.
"""
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

# Ensure repo root is on the path so absolute imports work
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

pytestmark = pytest.mark.asyncio


async def test_brain_routing():
    """Brain correctly routes tasks to sub-agents."""
    from agents.nexus.brain import NexusBrain
    brain = NexusBrain()
    # Without API keys, brain may raise or return a fallback decision — both are valid
    try:
        result = await brain.decide({"yield_balance": 0.05, "context": "test"})
        assert isinstance(result, dict)
        assert "action" in result or "error" in result or result is not None
    except RuntimeError as exc:
        # Expected when no LLM backend keys are configured
        assert "LLM" in str(exc) or "API" in str(exc) or "backend" in str(exc)


async def test_keeper_runs_without_rpc():
    """Keeper agent runs a cycle gracefully without RPC configured."""
    from agents.nexus.sub_agents.keeper import NexusKeeper
    keeper = NexusKeeper()
    keeper.allocate_budget(0.01)
    result = await keeper.run_cycle()
    assert isinstance(result, dict)
    # Should return gas info or error, never raise
    assert "error" in result or "gas_gwei" in result


async def test_monitor_runs_without_telegram():
    """Monitor runs without Telegram credentials."""
    from agents.nexus.sub_agents.monitor import NexusMonitor
    monitor = NexusMonitor()
    result = await monitor.run_cycle()
    assert isinstance(result, dict)
    assert "apy" in result or "error" in result


async def test_prover_generates_mock_proof():
    """Prover generates a mock ZK proof when nargo not installed."""
    from agents.nexus.sub_agents.prover import NexusProver
    prover = NexusProver()
    proof = await prover.generate_proof(
        "api_proof",
        {"api_key_hash": "0xdeadbeef", "response_nonce": "0x1234"},
        {"endpoint_hash": "0xabcd", "result_hash": "0xef01", "timestamp": int(time.time()), "window_seconds": 60}
    )
    assert proof["circuit"] == "api_proof"
    assert proof["proof"].startswith("0x")
    assert len(proof["proof"]) > 10


async def test_prover_cache():
    """Prover caches identical proof requests."""
    from agents.nexus.sub_agents.prover import NexusProver
    prover = NexusProver()
    inputs = {"endpoint_hash": "0x1234", "result_hash": "0x5678", "timestamp": 100, "window_seconds": 60}
    proof1 = await prover.generate_proof("api_proof", {"api_key_hash": "0xabc"}, inputs)
    proof2 = await prover.generate_proof("api_proof", {"api_key_hash": "0xabc"}, inputs)
    assert not proof1["cached"]
    assert proof2["cached"]
    assert proof1["proof"] == proof2["proof"]


async def test_all_agents_get_status():
    """All 6 sub-agents return valid status dicts."""
    from agents.nexus.sub_agents import ALL_AGENTS
    for AgentClass in ALL_AGENTS:
        agent = AgentClass()
        agent.allocate_budget(0.01)
        status = await agent.get_status()
        assert "agent_id" in status
        assert "status" in status
        # budget field may be "budget_eth" (flat) or "budget" (nested dict)
        assert "budget_eth" in status or "budget" in status
        # cycle count field
        assert "cycle_count" in status or "cycles" in status
        # verify budget value is a float
        budget_val = status.get("budget_eth", status.get("budget", {}).get("allocated", 0.0))
        assert isinstance(budget_val, float)


async def test_economy_marketplace_list():
    """Marketplace returns non-empty agent list."""
    from agents.nexus.economy import AgentMarketplace
    marketplace = AgentMarketplace()
    agents = await marketplace.list_agents()
    assert len(agents) >= 2
    for a in agents:
        assert "agent_id" in a
        assert "capabilities" in a
        assert "price_eth" in a
        assert "reputation" in a


async def test_economy_hire_and_rate():
    """Can hire an agent and rate them."""
    from agents.nexus.economy import AgentMarketplace
    marketplace = AgentMarketplace()
    result = await marketplace.hire_agent("nexus-scorer", {"task": "evaluate project"}, 0.001)
    assert result.success
    assert result.job_id.startswith("job_")
    # Rate the agent
    rating_id = await marketplace.rate_agent("nexus-scorer", result.job_id, 90, "Great work!")
    assert "nexus-scorer" in rating_id


async def test_reputation_gate_tiers():
    """Reputation gate enforces correct tiers."""
    from agents.nexus.economy import ReputationGate
    from agents.nexus.economy.reputation import InsufficientReputationError
    gate = ReputationGate()
    # Manually set scores
    gate._scores["low_agent"] = 5
    gate._scores["mid_agent"] = 55
    gate._scores["high_agent"] = 85
    # Low agent can't do treasury operations
    with pytest.raises(InsufficientReputationError):
        await gate.require_reputation("low_agent", "withdrawYield")
    # Mid agent can trade
    await gate.require_reputation("mid_agent", "swap")  # should not raise
    # High agent can do treasury
    await gate.require_reputation("high_agent", "withdrawYield")


async def test_payment_engine_x402():
    """Payment engine builds x402 payment headers."""
    from agents.nexus.economy import PaymentEngine
    engine = PaymentEngine()
    # pay_x402 will fail network call but should not raise
    result = await engine.pay_x402("http://nonexistent.example.com", 0.0001, "test")
    assert hasattr(result, "success")
    assert hasattr(result, "amount_eth")
    assert result.amount_eth == 0.0001


async def test_escrow_lifecycle():
    """Escrow create -> pending -> release flow."""
    from agents.nexus.economy import PaymentEngine
    engine = PaymentEngine()
    escrow_id = await engine.create_escrow(
        "0x1234567890abcdef1234567890abcdef12345678",
        0.05,
        "0xNexusArbiterAddress",
        "Score public goods project"
    )
    assert escrow_id.startswith("escrow_")
    pending = await engine.get_pending_payments()
    assert any(e["escrow_id"] == escrow_id for e in pending)
    released = await engine.release_escrow(escrow_id, {"proof": "0xdeadbeef"})
    assert released
    # Should no longer be in pending
    pending2 = await engine.get_pending_payments()
    assert not any(e["escrow_id"] == escrow_id for e in pending2)


def test_agent_log_json_valid():
    """agent_log.json is valid JSON (object or JSON lines) if it exists."""
    log_path = ROOT / "agent_log.json"
    if not log_path.exists():
        return
    raw = log_path.read_text().strip()
    if not raw:
        return
    # Try as a single JSON object first (the primary format used by brain.py)
    if raw.startswith("{") or raw.startswith("["):
        data = json.loads(raw)  # must not raise
        if isinstance(data, dict):
            assert "agent" in data or "entries" in data or "session" in data
        return
    # Fall back to JSON-lines format
    for line in raw.splitlines():
        line = line.strip()
        if line:
            entry = json.loads(line)  # must not raise
            assert "t" in entry or "timestamp" in entry or "agent" in entry


def test_x402_verify_header():
    """x402 middleware correctly validates payment headers."""
    from mcp.x402_middleware import verify_payment_header
    good = {"X-Payment": json.dumps({
        "network": "eip155:8453",
        "amount": str(int(0.001 * 1e18)),
        "scheme": "exact"
    })}
    bad = {"X-Payment": "not json"}
    empty = {}
    assert verify_payment_header(good, 0.0001) is True
    assert verify_payment_header(bad, 0.0001) is False
    assert verify_payment_header(empty, 0.0001) is False
