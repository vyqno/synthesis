"""Tests for NexusIdentity."""
import pytest
from agents.nexus.identity import NexusIdentity


def test_register_agent_identity():
    identity = NexusIdentity()
    result = identity.register_agent_identity("nexus-test", "0x1234567890abcdef1234567890abcdef12345678")
    assert "agent_id" in result
    assert result["name"] == "nexus-test"
    assert result["reputation"] == 50


def test_get_reputation_unknown():
    identity = NexusIdentity()
    result = identity.get_reputation("nonexistent_id")
    assert result["trust_level"] == "unknown"
    assert result["score"] == 0


def test_get_reputation_registered():
    identity = NexusIdentity()
    reg = identity.register_agent_identity("nexus-test", "0x" + "a" * 40)
    agent_id = reg["agent_id"]

    result = identity.get_reputation(agent_id)
    assert result["trust_level"] == "medium"  # score=50


def test_erc8128_token_issue_and_verify():
    identity = NexusIdentity()
    address = "0x" + "b" * 40

    token_result = identity.issue_erc8128_token(address, "read:treasury", expiry_seconds=3600)
    assert "bearer_token" in token_result
    assert token_result["scope"] == "read:treasury"

    verify_result = identity.verify_erc8128_token(token_result["bearer_token"])
    assert verify_result["valid"] is True
    assert verify_result["agent_address"] == address


def test_erc8128_token_invalid():
    identity = NexusIdentity()
    result = identity.verify_erc8128_token("invalid_token_xyz")
    assert result["valid"] is False


def test_format_address_truncation():
    identity = NexusIdentity()
    address = "0xabcdef1234567890abcdef1234567890abcdef12"
    # No ENS name registered, should truncate
    with pytest.MonkeyPatch().context() as m:
        m.setattr(identity, "reverse_resolve", lambda _: None)
        result = identity.format_address(address)
    assert "..." in result
    assert result.startswith("0xabcd")
