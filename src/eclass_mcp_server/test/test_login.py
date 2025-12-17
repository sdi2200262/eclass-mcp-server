"""Test login functionality for eClass MCP Server."""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from eclass_mcp_server.server import handle_login, handle_logout, session_state

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_login')


async def test_login() -> bool:
    """Test the login functionality."""
    print("Testing login functionality...")
    
    load_dotenv()
    
    username = os.getenv('ECLASS_USERNAME')
    password = os.getenv('ECLASS_PASSWORD')
    
    if not username or not password:
        print("ERROR: ECLASS_USERNAME and ECLASS_PASSWORD must be set in the .env file.")
        return False
    
    response = await handle_login()
    
    if not response:
        print("ERROR: Empty response from login handler.")
        return False
    
    text_content = response[0]
    print(f"Login response: {text_content.text}")
    
    if "Login successful" in text_content.text:
        print("Login test SUCCESS!")
        return True
    
    print("Login test FAILED!")
    return False


async def test_logout() -> bool:
    """Test the logout functionality."""
    if not session_state.logged_in:
        print("Not logged in, skipping logout test.")
        return False
    
    print("Testing logout functionality...")
    
    response = await handle_logout()
    
    if not response:
        print("ERROR: Empty response from logout handler.")
        return False
    
    text_content = response[0]
    print(f"Logout response: {text_content.text}")
    
    if "Successfully logged out" in text_content.text:
        print("Logout test SUCCESS!")
        return True
    
    print("Logout test FAILED!")
    return False


async def main() -> None:
    """Run login tests."""
    print("=== Starting eClass MCP Server Login Tests ===")
    
    login_success = await test_login()
    if login_success:
        await test_logout()
    
    print("=== Completed eClass MCP Server Login Tests ===")


if __name__ == "__main__":
    asyncio.run(main())
