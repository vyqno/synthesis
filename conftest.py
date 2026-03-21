"""
Root conftest.py — ensure installed mcp SDK takes precedence over local mcp/ directory.
Must run before any test imports mcp.
"""
import sys
from pathlib import Path

# The installed mcp SDK must come before the repo root in sys.path
# so that `from mcp.server import ...` resolves to the SDK, not our local mcp/ directory.
_site = str(Path.home() / ".local/lib/python3.12/site-packages")
if _site not in sys.path:
    sys.path.insert(0, _site)

# Clear any cached mcp modules so the correct one is found
for key in list(sys.modules.keys()):
    if key == "mcp" or key.startswith("mcp."):
        del sys.modules[key]
