"""
CoralCollective MCP (Model Context Protocol) Module

Provides integration with MCP servers for tool access.
"""

from typing import Optional

try:
    from .mcp_client import MCPClient
except ImportError:
    # MCP is optional
    class MCPClient:
        def __init__(self, config_path: Optional[str] = None):
            raise ImportError(
                "MCP support not installed. Install with: pip install coral-collective[mcp]"
            )

__all__ = ['MCPClient']