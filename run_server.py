#!/usr/bin/env python
"""Entry point script for eClass MCP Server."""

import asyncio
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.eclass_mcp_server.server import main

if __name__ == "__main__":
    asyncio.run(main())
