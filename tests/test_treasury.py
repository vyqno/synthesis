"""Tests for NexusTreasury."""
import pytest
from agents.nexus.treasury import NexusTreasury


def test_treasury_status_demo_mode():
    """Treasury should work in demo mode without a contract address."""
    treasury = NexusTreasury()
    treasury.contract = None  # Force demo mode

    status = treasury.get_treasury_status()
    assert "yield_balance_eth" in status
    assert status["yield_balance_eth"] > 0


def test_allocate_budget():
    treasury = NexusTreasury()
    treasury.contract = None

    result = treasury.allocate_budget("nexus-trader", 0.001)
    assert result["allocated"] == 0.001
    assert result["total_budget"] == 0.001


def test_allocate_budget_insufficient():
    treasury = NexusTreasury()
    treasury.contract = None
    # Try to allocate more than available yield
    with pytest.raises(ValueError, match="Insufficient yield"):
        treasury.allocate_budget("nexus-trader", 999.0)


def test_log_inference_spend():
    treasury = NexusTreasury()
    treasury.log_inference_spend("nexus-trader", "bankr/claude", 1000, 0.01)

    usage = treasury.get_bankr_usage()
    assert usage["total_spend_usd"] == pytest.approx(0.01)
    assert usage["funded_from_yield"] is True


def test_agent_budget_tracking():
    treasury = NexusTreasury()
    treasury.contract = None

    treasury.allocate_budget("nexus-scorer", 0.002)
    treasury.log_inference_spend("nexus-scorer", "venice", 500, 0.005)

    budget = treasury.get_agent_budget("nexus-scorer")
    assert budget["allocated_eth"] == pytest.approx(0.002)
    assert budget["spent_eth"] > 0
