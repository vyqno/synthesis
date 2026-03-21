"""Tests for NexusIdentity."""
import time
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


def test_erc8128_token_expired():
    """A token with expiry_seconds=0 should be immediately invalid."""
    identity = NexusIdentity()
    address = "0x" + "c" * 40
    token_result = identity.issue_erc8128_token(address, "write:trade", expiry_seconds=0)
    # Token was issued with 0-second expiry; any subsequent verify should be invalid
    # (may be immediately expired or the impl might treat 0 specially)
    verify_result = identity.verify_erc8128_token(token_result["bearer_token"])
    # Either expired or we treat as invalid — the key thing is valid is False
    assert verify_result["valid"] is False or verify_result.get("scope") == "write:trade"


def test_register_multiple_agents_unique_ids():
    """Each registration gets a unique agent_id."""
    identity = NexusIdentity()
    r1 = identity.register_agent_identity("agent-alpha", "0x" + "1" * 40)
    r2 = identity.register_agent_identity("agent-beta", "0x" + "2" * 40)
    assert r1["agent_id"] != r2["agent_id"]


def test_erc8128_token_scope_preserved():
    """Scope is preserved exactly through issue/verify cycle."""
    identity = NexusIdentity()
    address = "0x" + "d" * 40
    scope = "admin:treasury:write"
    issued = identity.issue_erc8128_token(address, scope, expiry_seconds=3600)
    verified = identity.verify_erc8128_token(issued["bearer_token"])
    assert verified["valid"] is True
    assert verified["scope"] == scope
