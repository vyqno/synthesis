"""Tests for NexusBrain — uses mocks, does not call real LLM APIs."""
import json
import pytest
from unittest.mock import patch, MagicMock
from agents.nexus.brain import NexusBrain, log_action


def test_log_action_creates_file(tmp_path, monkeypatch):
    """log_action should create agent_log.json if it doesn't exist."""
    import agents.nexus.brain as brain_module
    log_file = tmp_path / "agent_log.json"
    monkeypatch.setattr(brain_module, "LOG_FILE", log_file)

    log_action("test_action", "test_result")

    assert log_file.exists()
    log = json.loads(log_file.read_text())
    assert len(log["entries"]) == 1
    assert log["entries"][0]["action"] == "test_action"


def test_log_action_appends_multiple_entries(tmp_path, monkeypatch):
    """log_action should append successive entries."""
    import agents.nexus.brain as brain_module
    log_file = tmp_path / "agent_log.json"
    monkeypatch.setattr(brain_module, "LOG_FILE", log_file)

    log_action("first", "result_a")
    log_action("second", "result_b")

    log = json.loads(log_file.read_text())
    assert len(log["entries"]) == 2
    assert log["entries"][1]["action"] == "second"


def test_log_action_records_tool_and_params(tmp_path, monkeypatch):
    """log_action should record optional tool and params fields."""
    import agents.nexus.brain as brain_module
    log_file = tmp_path / "agent_log.json"
    monkeypatch.setattr(brain_module, "LOG_FILE", log_file)

    log_action("trade", {"status": "ok"}, tool="uniswap", params={"amount": 0.01})

    log = json.loads(log_file.read_text())
    entry = log["entries"][0]
    assert entry["tool"] == "uniswap"
    assert entry["params"]["amount"] == 0.01


def test_brain_routes_task():
    """route_task should return a valid sub-agent name."""
    brain = NexusBrain()
    with patch.object(brain, "decide", return_value="nexus-trader"):
        result = brain.route_task("swap 1 ETH for USDC")
    assert result == "nexus-trader"


def test_brain_raises_without_keys():
    """Brain should raise RuntimeError if no LLM keys configured."""
    brain = NexusBrain()
    brain.bankr_key = ""
    brain.venice_key = ""
    brain.groq_key = ""

    with pytest.raises(RuntimeError, match="No LLM backend"):
        brain.decide("test task")


def test_brain_reason_privately_raises_without_venice_key():
    """reason_privately should raise RuntimeError if no Venice key set."""
    brain = NexusBrain()
    brain.venice_key = ""

    with pytest.raises(RuntimeError, match="Venice API key"):
        brain.reason_privately("sensitive task")


def test_brain_decide_uses_bankr_first():
    """When bankr_key is set, brain should try Bankr first."""
    brain = NexusBrain()
    brain.bankr_key = "fake-bankr-key"
    brain.venice_key = ""
    brain.groq_key = ""

    with patch.object(brain, "_chat", return_value="do-the-swap") as mock_chat:
        result = brain.decide("swap ETH")

    assert result == "do-the-swap"
    # _chat was called with Bankr base URL
    call_args = mock_chat.call_args
    assert brain.BANKR_BASE in call_args[0]


def test_brain_falls_back_to_venice_when_bankr_fails():
    """Brain should fall back to Venice when Bankr raises."""
    brain = NexusBrain()
    brain.bankr_key = "fake-bankr-key"
    brain.venice_key = "fake-venice-key"
    brain.groq_key = ""

    call_count = {"n": 0}

    def side_effect(base_url, api_key, model, messages, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise Exception("Bankr unavailable")
        return "venice-response"

    with patch.object(brain, "_chat", side_effect=side_effect):
        result = brain.decide("complex task")

    assert result == "venice-response"
    assert call_count["n"] == 2


def test_brain_get_compute_budget_returns_float():
    """get_compute_budget should return a float even without a live contract."""
    brain = NexusBrain()
    budget = brain.get_compute_budget()
    assert isinstance(budget, float)
    assert budget >= 0.0
