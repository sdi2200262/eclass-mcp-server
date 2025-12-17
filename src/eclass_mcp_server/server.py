"""
eClass MCP Server - MCP Integration for Open eClass Platform

Provides an MCP server for interacting with eClass through UoA's SSO authentication.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from . import authentication
from . import course_management
from . import html_parsing

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('eclass_mcp_server')

server = Server("eclass-mcp")


class SessionState:
    """Maintains authentication state between MCP tool calls."""
    
    def __init__(self) -> None:
        # Load .env from project root
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        env_path = os.path.join(project_root, '.env')
        load_dotenv(env_path, override=False)
        
        self.session = requests.Session()
        self.logged_in = False
        
        # Base URL configuration
        self.base_url = os.getenv('ECLASS_URL', 'https://eclass.uoa.gr').rstrip('/')
        self.eclass_domain = urlparse(self.base_url).netloc
        
        # SSO configuration
        self.sso_domain = os.getenv('ECLASS_SSO_DOMAIN', 'sso.uoa.gr')
        sso_protocol = os.getenv('ECLASS_SSO_PROTOCOL', 'https')
        self.sso_base_url = f"{sso_protocol}://{self.sso_domain}"
        
        # eClass endpoint URLs
        self.login_form_url = f"{self.base_url}/main/login_form.php"
        self.portfolio_url = f"{self.base_url}/main/portfolio.php"
        self.logout_url = f"{self.base_url}/index.php?logout=yes"
        
        self.username: str | None = None
        self.courses: List[Dict[str, str]] = []
        
        logger.info(f"Initialized eClass session for {self.base_url} (SSO: {self.sso_domain})")
    
    def is_session_valid(self) -> bool:
        """Check if the current session is still valid."""
        if not self.logged_in:
            return False
        
        try:
            response = self.session.get(self.portfolio_url, allow_redirects=False)
            if response.status_code == 302 and 'login' in response.headers.get('Location', ''):
                self.logged_in = False
                return False
            if response.status_code == 200 and html_parsing.verify_login_success(response.text):
                return True
            self.logged_in = False
            return False
        except Exception:
            self.logged_in = False
            return False
    
    def reset(self) -> None:
        """Reset the session state."""
        self.session = requests.Session()
        self.logged_in = False
        self.username = None
        self.courses = []


session_state = SessionState()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available eClass tools."""
    return [
        types.Tool(
            name="login",
            description="Log in to eClass using username/password from your .env file through UoA's SSO. Configure ECLASS_USERNAME and ECLASS_PASSWORD in your .env file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "random_string": {
                        "type": "string",
                        "description": "Dummy parameter for no-parameter tools"
                    },
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
                    "random_string": {
                        "type": "string",
                        "description": "Dummy parameter for no-parameter tools"
                    },
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
                    "random_string": {
                        "type": "string",
                        "description": "Dummy parameter for no-parameter tools"
                    },
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
                    "random_string": {
                        "type": "string",
                        "description": "Dummy parameter for no-parameter tools"
                    },
                },
                "required": ["random_string"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any] | None
) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle eClass tool execution requests."""
    if name == "login":
        return await handle_login()
    elif name == "get_courses":
        return await handle_get_courses()
    elif name == "logout":
        return await handle_logout()
    elif name == "authstatus":
        return await handle_authstatus()
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_login() -> List[types.TextContent]:
    """Handle login to eClass."""
    if session_state.logged_in and session_state.is_session_valid():
        return [
            types.TextContent(
                type="text",
                text=f"Already logged in as {session_state.username}",
            )
        ]
    
    if session_state.logged_in and not session_state.is_session_valid():
        session_state.reset()
    
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
    success, message = authentication.attempt_login(session_state, username, password)
    return [authentication.format_login_response(success, message, username if success else None)]


async def handle_get_courses() -> List[types.TextContent]:
    """Handle getting the list of enrolled courses."""
    success, message, courses = course_management.get_courses(session_state)
    return [course_management.format_courses_response(success, message, courses)]


async def handle_logout() -> List[types.TextContent]:
    """Handle logout from eClass."""
    success, username_or_error = authentication.perform_logout(session_state)
    return [authentication.format_logout_response(success, username_or_error)]


async def handle_authstatus() -> List[types.TextContent]:
    """Handle checking authentication status."""
    return [authentication.format_authstatus_response(session_state)]


async def main() -> None:
    """Run the MCP server."""
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