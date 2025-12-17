"""eClass MCP Server - MCP integration for Open eClass platform."""

import asyncio

from . import server

__all__ = ['main', 'server']


def main() -> None:
    """Main entry point for the package."""
    asyncio.run(server.main())
