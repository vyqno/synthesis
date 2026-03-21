# Minimal stub — real imports come from the installed mcp SDK.
# When sys.path includes site-packages before the repo root, the installed
# mcp.server module resolves correctly. See tests/integration/test_mcp_servers.py.

class Server:
    """Stub — replaced by installed mcp.server.Server at runtime."""
    def __init__(self, name): self.name = name

__all__ = ["Server"]
