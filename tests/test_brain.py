"""Tests for NexusBrain — uses mocks, does not call real LLM APIs."""
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
    import json
    log = json.loads(log_file.read_text())
    assert len(log["entries"]) == 1
    assert log["entries"][0]["action"] == "test_action"


def test_brain_routes_task():
    """route_task should return a valid sub-agent name."""
    brain = NexusBrain()
    # Mock the decide method
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
