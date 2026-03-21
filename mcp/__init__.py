# Namespace package: extends __path__ so both local mcp/ servers
# AND the installed mcp SDK (mcp.server, mcp.client, etc.) are accessible.
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)
