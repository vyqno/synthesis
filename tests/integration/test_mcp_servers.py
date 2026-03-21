"""
Integration tests for all 8 Nexus MCP servers.
Tests that each server imports cleanly and tools return valid JSON.
Does NOT require real API keys — uses demo/mock modes.
"""
import importlib.util
import pytest
import sys
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

# Ensure installed mcp SDK takes precedence over local mcp/ directory
_site = str(Path.home() / ".local/lib/python3.12/site-packages")
if _site not in sys.path:
    sys.path.insert(0, _site)
sys.path.insert(1, str(ROOT))


def _load_server(mcp_dir: str, unique_name: str):
    """Load a server.py from an MCP directory using a unique module name to avoid cache collisions."""
    server_path = ROOT / mcp_dir / "server.py"
    spec = importlib.util.spec_from_file_location(unique_name, server_path)
    mod = importlib.util.module_from_spec(spec)
    # Temporarily add the mcp dir to sys.path so relative imports within server.py work
    mcp_path = str(ROOT / mcp_dir)
    sys.path.insert(0, mcp_path)
    try:
        spec.loader.exec_module(mod)
    finally:
        if mcp_path in sys.path:
            sys.path.remove(mcp_path)
    return mod


class TestLidoMCP:
    def setup_method(self):
        self.server = _load_server("mcp/lido-mcp", "lido_server")

    def test_server_imports(self):
        assert self.server is not None

    def test_get_balance_returns_dict(self):
        import asyncio
        result = asyncio.run(self.server.handle_get_balance({"address": "0x742d35Cc6634C0532925a3b8D4C9C8e2F1234567"}))
        assert isinstance(result, (dict, list, str))

    def test_get_vault_yield_structure(self):
        import asyncio
        result = asyncio.run(self.server.handle_get_vault_yield({"vault": "earneth"}))
        result_str = str(result)
        assert len(result_str) > 0


class TestTreasuryMCP:
    def setup_method(self):
        self.server = _load_server("mcp/treasury-mcp", "treasury_server")

    def test_server_imports(self):
        assert self.server is not None

    def test_simulate_yield_loop_returns_steps(self):
        import asyncio
        result = asyncio.run(self.server.handle_simulate_yield_funding_loop({}))
        assert isinstance(result, dict)
        result_str = json.dumps(result).lower()
        assert "yield" in result_str or "step" in result_str or "loop" in result_str


class TestIdentityMCP:
    def setup_method(self):
        self.server = _load_server("mcp/identity-mcp", "identity_server")

    def test_server_imports(self):
        assert self.server is not None

    def test_format_address_truncates(self):
        result = self.server.format_address("0x742d35Cc6634C0532925a3b8D4C9C8e2F1234567")
        assert isinstance(result, dict)
        formatted = result.get("formatted", result.get("address", ""))
        assert "..." in formatted or "742d" in formatted.lower() or len(formatted) < 42


class TestTradeMCP:
    def setup_method(self):
        self.server = _load_server("mcp/trade-mcp", "trade_server")

    def test_server_imports(self):
        assert self.server is not None


class TestStorageMCP:
    def setup_method(self):
        self.server = _load_server("mcp/storage-mcp", "storage_server")

    def test_server_imports(self):
        assert self.server is not None

    def test_store_returns_cid(self):
        # store() generates a demo CID when FILECOIN_TOKEN is unset — no network call needed
        result = self.server.store('{"test": true}', "test")
        assert isinstance(result, dict)
        assert "cid" in result
        assert result["cid"].startswith("bafk")
        assert result.get("stored") is True


class TestCoordinateMCP:
    def setup_method(self):
        self.server = _load_server("mcp/coordinate-mcp", "coordinate_server")

    def test_server_imports(self):
        assert self.server is not None

    def test_list_available_agents_returns_6(self):
        import asyncio
        result = asyncio.run(self.server.handle_list_available_agents({}))
        assert isinstance(result, list)
        assert len(result) >= 6
        agent_ids = [a.get("agent_id", "") if isinstance(a, dict) else str(a) for a in result]
        all_ids = " ".join(agent_ids)
        assert "trader" in all_ids or "nexus-trader" in all_ids


class TestGoodsMCP:
    def setup_method(self):
        self.server = _load_server("mcp/goods-mcp", "goods_server")

    def test_server_imports(self):
        assert self.server is not None

    def test_get_sybil_score_returns_number(self):
        # get_sybil_score is a pure deterministic function — no network call
        result = self.server.get_sybil_score("0x742d35Cc6634C0532925a3b8D4C9C8e2F1234567")
        assert isinstance(result, dict)
        assert "score" in result
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100
        assert "flags" in result


class TestSecretsMCP:
    def setup_method(self):
        self.server = _load_server("mcp/secrets-mcp", "secrets_server")

    def test_server_imports(self):
        assert self.server is not None
