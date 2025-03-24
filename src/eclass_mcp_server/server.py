"""
eClass MCP Server - MCP Integration for Open eClass Platform

This module provides an MCP server for interacting with an eClass platform instance.
It handles authentication, session management, and course access for eClass resources.
Specifically tailored for UoA's SSO authentication system.
"""

import asyncio
import os
import logging
import re
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

# Import from modularized components
from . import authentication
from . import course_management
from . import html_parsing

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('eclass_mcp_server')

# Initialize the MCP server
server = Server("eclass-mcp")

# Global session state - maintains authentication state between calls
class SessionState:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize session and state
        self.session = requests.Session()
        self.logged_in = False
        
        # Set base URL
        self.base_url = os.getenv('ECLASS_URL')
        if not self.base_url:
            self.base_url = "https://eclass.uoa.gr"
            logger.warning(f"ECLASS_URL not set in environment, using default: {self.base_url}")
        
        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip('/')
        
        # Set SSO URLs
        self.login_form_url = f"{self.base_url}/main/login_form.php"
        self.portfolio_url = f"{self.base_url}/main/portfolio.php"
        self.logout_url = f"{self.base_url}/index.php?logout=yes"
        
        # Store user information
        self.username = None
        self.courses = []
        
        logger.info(f"Initialized eClass session for {self.base_url}")
    
    def is_session_valid(self) -> bool:
        """Check if the current session is still valid without full re-auth."""
        if not self.logged_in:
            return False
        
        try:
            # Try accessing a protected resource that requires authentication
            response = self.session.get(self.portfolio_url, allow_redirects=False)
            # If we get redirected to login page, session is invalid
            if response.status_code == 302 and 'login' in response.headers.get('Location', ''):
                self.logged_in = False
                return False
            # Check for successful access to the portfolio page
            if response.status_code == 200:
                if html_parsing.verify_login_success(response.text):
                    return True
            # Session is invalid
            self.logged_in = False
            return False
        except:
            self.logged_in = False
            return False
    
    def reset(self):
        """Reset the session state."""
        self.session = requests.Session()
        self.logged_in = False
        self.username = None
        self.courses = []

# Initialize global session state
session_state = SessionState()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available eClass tools.
    """
    return [
        types.Tool(
            name="login",
            description="Log in to eClass using username/password from your .env file through UoA's SSO. Configure ECLASS_USERNAME and ECLASS_PASSWORD in your .env file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "random_string": {"type": "string", "description": "Dummy parameter for no-parameter tools"},
                },
                "required": ["random_string"],
            },
        ),
        types.Tool(
            name="get_courses",
            description="Get list of enrolled courses from eClass",
            inputSchema={
                "type": "object",
                "properties": {
                    "random_string": {"type": "string", "description": "Dummy parameter for no-parameter tools"},
                },
                "required": ["random_string"],
            },
        ),
        types.Tool(
            name="logout",
            description="Log out from eClass",
            inputSchema={
                "type": "object",
                "properties": {
                    "random_string": {"type": "string", "description": "Dummy parameter for no-parameter tools"},
                },
                "required": ["random_string"],
            },
        ),
        types.Tool(
            name="authstatus",
            description="Check authentication status with eClass",
            inputSchema={
                "type": "object",
                "properties": {
                    "random_string": {"type": "string", "description": "Dummy parameter for no-parameter tools"},
                },
                "required": ["random_string"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any] | None
) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle eClass tool execution requests.
    """
    if name == "login":
        return await handle_login({})
    elif name == "get_courses":
        return await handle_get_courses()
    elif name == "logout":
        return await handle_logout()
    elif name == "authstatus":
        return await handle_authstatus()
    else:
        raise ValueError(f"Unknown tool: {name}")

async def handle_login(arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle login to eClass."""
    # Check if already logged in
    if session_state.logged_in and session_state.is_session_valid():
        return [
            types.TextContent(
                type="text",
                text=f"Already logged in as {session_state.username}",
            )
        ]
    
    # Reset session if needed
    if session_state.logged_in and not session_state.is_session_valid():
        session_state.reset()
    
    # Get credentials from environment variables
    username = os.getenv('ECLASS_USERNAME')
    password = os.getenv('ECLASS_PASSWORD')
    
    if not username or not password:
        return [
            types.TextContent(
                type="text",
                text="Error: Username and password must be provided in the .env file. Please set ECLASS_USERNAME and ECLASS_PASSWORD in your .env file.",
            )
        ]
    
    logger.info(f"Attempting to log in as {username}")
    
    # Attempt login using the authentication module
    success, message = authentication.attempt_login(session_state, username, password)
    
    # Format and return the response
    return [authentication.format_login_response(success, message, username if success else None)]

async def handle_get_courses() -> List[types.TextContent]:
    """Handle getting the list of enrolled courses."""
    # Use the course_management module to get courses
    success, message, courses = course_management.get_courses(session_state)
    
    # Format and return the response
    return [course_management.format_courses_response(success, message, courses)]

async def handle_logout() -> List[types.TextContent]:
    """Handle logout from eClass."""
    # Use the authentication module to perform logout
    success, username_or_error = authentication.perform_logout(session_state)
    
    # Format and return the response
    return [authentication.format_logout_response(success, username_or_error)]

async def handle_authstatus() -> List[types.TextContent]:
    """Handle checking authentication status."""
    # Use the authentication module to format the status response
    return [authentication.format_authstatus_response(session_state)]

async def main():
    """Run the MCP server."""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="eclass-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())