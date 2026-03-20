"""
Integration tests for Nexus agent modules.
"""
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


def test_brain_import():
    from agents.nexus.brain import NexusBrain, log_action
    brain = NexusBrain()
    assert brain is not None
    assert hasattr(brain, 'decide')
    assert hasattr(brain, 'reason_privately')
    assert hasattr(brain, 'route_task')


def test_brain_no_keys_raises():
    from agents.nexus.brain import NexusBrain
    brain = NexusBrain()
    brain.bankr_key = ""
    brain.venice_key = ""
    brain.groq_key = ""
    with pytest.raises(RuntimeError):
        brain.decide("test")


def test_identity_ens_demo_fallback():
    from agents.nexus.identity import NexusIdentity
    identity = NexusIdentity()
    # Should not crash even without network
    result = identity.register_agent_identity("test-agent", "0x" + "a" * 40)
    assert result["name"] == "test-agent"
    assert result["reputation"] == 50


def test_identity_erc8128_full_lifecycle():
    from agents.nexus.identity import NexusIdentity
    identity = NexusIdentity()
    issued = identity.issue_erc8128_token("0x" + "b" * 40, "read:treasury", 3600)
    assert "bearer_token" in issued
    verified = identity.verify_erc8128_token(issued["bearer_token"])
    assert verified["valid"] is True
    assert verified["scope"] == "read:treasury"


def test_treasury_yield_budget_allocation():
    from agents.nexus.treasury import NexusTreasury
    t = NexusTreasury()
    t.contract = None  # Demo mode
    status = t.get_treasury_status()
    assert "yield_balance_eth" in status
    assert status["yield_balance_eth"] > 0
    result = t.allocate_budget("nexus-trader", 0.001)
    assert result["allocated"] == 0.001


def test_wallet_ows_policy_check():
    from agents.nexus.wallet import check_policy, DEFAULT_POLICY
    # Under cap: allowed
    result = check_policy("swap", 0.005)
    assert result["allowed"] is True
    # Over cap: denied
    result = check_policy("swap", 100.0)
    assert result["allowed"] is False


def test_wallet_chain_plugins_present():
    from agents.nexus.wallet import CHAIN_PLUGINS
    assert "ethereum" in CHAIN_PLUGINS
    assert "base" in CHAIN_PLUGINS
    assert "arbitrum" in CHAIN_PLUGINS
    assert "celo" in CHAIN_PLUGINS


def test_agent_log_json_exists():
    import json
    log_path = ROOT / "agent_log.json"
    assert log_path.exists(), "agent_log.json must exist"
    log = json.loads(log_path.read_text())
    assert "entries" in log
    assert len(log["entries"]) >= 20, "Need at least 20 log entries for judges"


def test_agent_json_structure():
    import json
    manifest = json.loads((ROOT / "agent.json").read_text())
    assert manifest["tracks_submitted"] == 46
    assert len(manifest["mcp_servers"]) == 8
    assert len(manifest["chains"]) >= 5
    assert "openclaw_skill" in manifest


def test_skills_all_present():
    skills_dir = ROOT / "skills"
    expected = ["nexus", "lido", "treasury", "identity", "trade",
                "coordinate", "goods", "secrets", "storage"]
    for skill in expected:
        assert (skills_dir / f"{skill}.skill.md").exists(), f"Missing {skill}.skill.md"
    assert (ROOT / "nexus.skill.md").exists(), "nexus.skill.md missing from repo root"
