"""
Tests for Nexus sub-agents: NexusTrader, NexusStaker, NexusScorer, SubAgent base.
All tests use mocking to avoid real network calls.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ──────────────────────────────────────────────────────────────────────────────
# SubAgent base class behaviour
# ──────────────────────────────────────────────────────────────────────────────

class TestSubAgentBase:
    """Tests for the shared SubAgent base class via NexusScorer (simplest concrete)."""

    def setup_method(self):
        from agents.nexus.sub_agents.scorer import NexusScorer
        self.agent = NexusScorer()

    def test_initial_budget_is_zero(self):
        assert self.agent.budget_eth == 0.0

    def test_allocate_budget_increases_balance(self):
        self.agent.allocate_budget(0.05)
        assert self.agent.budget_eth == pytest.approx(0.05)

    def test_allocate_budget_is_additive(self):
        self.agent.allocate_budget(0.01)
        self.agent.allocate_budget(0.02)
        assert self.agent.budget_eth == pytest.approx(0.03)

    def test_deduct_budget_returns_true_when_sufficient(self):
        self.agent.allocate_budget(0.1)
        result = self.agent.deduct_budget(0.05, reason="test")
        assert result is True
        assert self.agent.budget_eth == pytest.approx(0.05)

    def test_deduct_budget_returns_false_when_insufficient(self):
        self.agent.allocate_budget(0.01)
        result = self.agent.deduct_budget(0.1, reason="test")
        assert result is False
        assert self.agent.budget_eth == pytest.approx(0.01)  # unchanged

    def test_initial_status_is_idle(self):
        assert self.agent.status == "idle"

    def test_set_status_updates_status(self):
        self.agent.set_status("running")
        assert self.agent.status == "running"

    def test_get_status_contains_required_keys(self):
        status = asyncio.run(self.agent.get_status())
        assert "agent_id" in status
        assert "status" in status
        assert "budget_eth" in status
        assert "cycle_count" in status
        assert "uptime_seconds" in status

    def test_action_log_is_empty_initially(self):
        assert self.agent.action_log == []


# ──────────────────────────────────────────────────────────────────────────────
# NexusTrader
# ──────────────────────────────────────────────────────────────────────────────

class TestNexusTrader:
    def setup_method(self):
        from agents.nexus.sub_agents.trader import NexusTrader
        self.trader = NexusTrader()
        self.trader.allocate_budget(0.1)

    def test_calc_dca_amount_is_10pct_of_budget(self):
        amount = self.trader._calc_dca_amount()
        assert amount == pytest.approx(0.01)  # 10% of 0.1

    def test_calc_dca_amount_zero_when_no_budget(self):
        from agents.nexus.sub_agents.trader import NexusTrader
        trader = NexusTrader()
        assert trader._calc_dca_amount() == 0.0

    def test_record_price_adds_to_history(self):
        self.trader._record_price(3000.0)
        assert len(self.trader._price_history) == 1
        assert self.trader._last_price_usd == 3000.0

    def test_calc_1h_change_none_with_insufficient_data(self):
        self.trader._record_price(3000.0)
        # Only one data point just added — no 1h-old data
        result = self.trader._calc_1h_change()
        assert result is None

    def test_execute_trade_simulation_mode(self):
        """execute_trade should return simulated result when no private key."""
        self.trader.private_key = ""
        result = asyncio.run(self.trader.execute_trade(
            "0xUSDA",
            "0xETH",
            0.01,
        ))
        assert result["status"] == "simulated"
        assert result["amount_eth"] == pytest.approx(0.01)

    def test_execute_trade_enforces_20pct_cap(self):
        """execute_trade should cap amount at 20% of budget."""
        self.trader.private_key = ""
        initial_budget = self.trader.budget_eth  # 0.1
        cap = initial_budget * 0.20  # 0.02
        # Try to trade 0.5 ETH but cap limits it to 0.02
        result = asyncio.run(self.trader.execute_trade("0xA", "0xB", 0.5))
        assert result["amount_eth"] == pytest.approx(cap)

    def test_execute_trade_skip_when_zero_amount(self):
        """execute_trade should skip when amount resolves to zero."""
        from agents.nexus.sub_agents.trader import NexusTrader
        trader = NexusTrader()
        # No budget — cap is 0, so amount becomes 0
        result = asyncio.run(trader.execute_trade("0xA", "0xB", 0.001))
        assert result["status"] == "skip"

    def test_run_cycle_returns_valid_dict_structure(self):
        """run_cycle always returns a dict with an 'action' key."""
        result = asyncio.run(self.trader.run_cycle())
        assert isinstance(result, dict)
        assert "action" in result
        # Valid actions for the trader cycle
        valid_actions = {"skip", "observe", "dca_buy", "gmx_long", "error"}
        assert result["action"] in valid_actions


# ──────────────────────────────────────────────────────────────────────────────
# NexusStaker
# ──────────────────────────────────────────────────────────────────────────────

class TestNexusStaker:
    def setup_method(self):
        from agents.nexus.sub_agents.staker import NexusStaker
        self.staker = NexusStaker()

    def test_min_apy_threshold_default(self):
        assert self.staker.min_apy_threshold == 3.0

    def test_rebalance_holds_when_apy_above_threshold(self):
        with patch.object(self.staker, "get_steth_apy", new=AsyncMock(return_value=4.5)):
            result = asyncio.run(self.staker.rebalance_position())
        assert result["action"] == "hold"
        assert result["apy"] == 4.5

    def test_rebalance_triggers_unstake_when_apy_below_threshold(self):
        with patch.object(self.staker, "get_steth_apy", new=AsyncMock(return_value=2.0)):
            result = asyncio.run(self.staker.rebalance_position())
        assert result["action"] == "unstake_triggered"
        assert result["dry_run"] is True

    def test_get_steth_apy_fallback(self):
        """get_steth_apy returns 4.0 fallback when network fails."""
        async def _bad_get(*args, **kwargs):
            raise ConnectionError("no network")

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(side_effect=ConnectionError("no network"))
            result = asyncio.run(self.staker.get_steth_apy())
        assert result == 4.0

    def test_status_includes_apy_fields(self):
        status = asyncio.run(self.staker.get_status())
        assert "current_apy" in status
        assert "min_apy_threshold" in status


# ──────────────────────────────────────────────────────────────────────────────
# NexusScorer
# ──────────────────────────────────────────────────────────────────────────────

class TestNexusScorer:
    def setup_method(self):
        from agents.nexus.sub_agents.scorer import NexusScorer
        self.scorer = NexusScorer()

    def test_run_cycle_returns_heartbeat(self):
        result = asyncio.run(self.scorer.run_cycle())
        assert isinstance(result, dict)
        # After run_cycle, status may be "idle" (reset by base class) or "waiting_for_requests"
        assert "status" in result or "olas_registered" in result

    def test_evaluate_project_returns_defaults_without_api_key(self):
        """evaluate_project returns defaults when VENICE_API_KEY is not set."""
        self.scorer.venice_api_key = ""
        result = asyncio.run(self.scorer.evaluate_project("https://example.com"))
        assert "impact" in result
        assert "legitimacy" in result
        assert "recommendation" in result
        assert "red_flags" in result
        assert result["impact"] == 50
        assert result["legitimacy"] == 50

    def test_serve_olas_request_routes_to_evaluate(self):
        """serve_olas_request should call evaluate_project and return result dict."""
        self.scorer.venice_api_key = ""
        result = asyncio.run(self.scorer.serve_olas_request({
            "project_url": "https://public-goods.example.com"
        }))
        assert "impact" in result
        assert result["project_url"] == "https://public-goods.example.com"


# ──────────────────────────────────────────────────────────────────────────────
# NexusProver
# ──────────────────────────────────────────────────────────────────────────────

class TestNexusProver:
    def setup_method(self):
        from agents.nexus.sub_agents.prover import NexusProver
        self.prover = NexusProver()

    def test_generate_proof_returns_hex_string(self):
        result = asyncio.run(self.prover.generate_proof(
            "api_proof",
            {"api_key_hash": "0xdeadbeef", "response_nonce": "0x1234"},
            {"endpoint_hash": "0xabcd", "result_hash": "0xef01",
             "timestamp": 1000000, "window_seconds": 60},
        ))
        assert result["proof"].startswith("0x")
        assert len(result["proof"]) > 10
        assert result["circuit"] == "api_proof"

    def test_second_identical_request_is_cached(self):
        inputs = {"endpoint_hash": "0x1", "result_hash": "0x2",
                  "timestamp": 999, "window_seconds": 30}
        p1 = asyncio.run(self.prover.generate_proof("api_proof", {"api_key_hash": "0xabc"}, inputs))
        p2 = asyncio.run(self.prover.generate_proof("api_proof", {"api_key_hash": "0xabc"}, inputs))
        assert p1["cached"] is False
        assert p2["cached"] is True
        assert p1["proof"] == p2["proof"]
