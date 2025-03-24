#!/usr/bin/env python
"""
Entry point script for eClass MCP Server

This script provides a direct entry point to run the eClass MCP server.
It's designed to make it easier to run the server from tools like Cursor.
"""

import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the main function from the server module
from src.eclass_mcp_server.server import main

if __name__ == "__main__":
    # Run the server
    asyncio.run(main()) 