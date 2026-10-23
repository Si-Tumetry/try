from core.services.talent import TalentService
from mcp_server.app import build_mcp
from mcp_server.auth import BearerAuthMiddleware, TokenStore


def create_asgi_app(service: TalentService, tokens: TokenStore):
    """MCP endpoint at /mcp, behind bearer-token authentication (ARCHITECTURE.md §5.2)."""
    mcp = build_mcp(service)
    return BearerAuthMiddleware(mcp.streamable_http_app(), tokens)
