"""
Test script for verifying eClass MCP Server login functionality.

This script tests the login functionality of the eClass MCP Server.
It attempts to log in using credentials from .env file and verifies the response.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from eclass_mcp_server.server import session_state, handle_login

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_login')

async def test_login():
    """Test the login functionality."""
    print("Testing login functionality...")
    
    # Load environment variables
    load_dotenv()
    
    # Check if credentials are set
    username = os.getenv('ECLASS_USERNAME')
    password = os.getenv('ECLASS_PASSWORD')
    
    if not username or not password:
        print("ERROR: ECLASS_USERNAME and ECLASS_PASSWORD must be set in the .env file.")
        return False
    
    # Attempt login
    response = await handle_login({})
    
    # Check response
    if not response or len(response) == 0:
        print("ERROR: Empty response from login handler.")
        return False
    
    text_content = response[0]
    print(f"Login response: {text_content.text}")
    
    # Check if login was successful
    if "Login successful" in text_content.text:
        print("Login test SUCCESS! ✅")
        return True
    else:
        print("Login test FAILED! ❌")
        return False

async def test_logout():
    """Test the logout functionality."""
    if not session_state.logged_in:
        print("Not logged in, skipping logout test.")
        return False
        
    # We need to import handle_logout here to prevent circular imports
    from eclass_mcp_server.server import handle_logout
    
    print("Testing logout functionality...")
    
    # Attempt logout
    response = await handle_logout()
    
    # Check response
    if not response or len(response) == 0:
        print("ERROR: Empty response from logout handler.")
        return False
    
    text_content = response[0]
    print(f"Logout response: {text_content.text}")
    
    # Check if logout was successful
    if "Successfully logged out" in text_content.text:
        print("Logout test SUCCESS! ✅")
        return True
    else:
        print("Logout test FAILED! ❌")
        return False

async def main():
    """Run all tests."""
    print("=== Starting eClass MCP Server Login Tests ===")
    
    login_success = await test_login()
    
    if login_success:
        await test_logout()
    
    print("=== Completed eClass MCP Server Login Tests ===")

if __name__ == "__main__":
    asyncio.run(main()) 