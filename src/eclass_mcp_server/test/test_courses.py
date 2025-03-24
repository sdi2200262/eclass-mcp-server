"""
Test script for verifying eClass MCP Server course retrieval functionality.

This script tests the course retrieval functionality of the eClass MCP Server.
It first logs in, then attempts to retrieve the list of enrolled courses.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from eclass_mcp_server.server import session_state, handle_login, handle_get_courses

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_courses')

async def ensure_login():
    """Ensure that we are logged in before testing course retrieval."""
    if session_state.logged_in and session_state.is_session_valid():
        print("Already logged in, proceeding with tests.")
        return True
    
    print("Not logged in, attempting login...")
    
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
    
    # Check if login was successful
    if response and "Login successful" in response[0].text:
        print("Login successful, proceeding with tests.")
        return True
    else:
        print("Login failed, cannot proceed with course tests.")
        return False

async def test_get_courses():
    """Test the course retrieval functionality."""
    print("Testing course retrieval functionality...")
    
    # Attempt to get courses
    response = await handle_get_courses()
    
    # Check response
    if not response or len(response) == 0:
        print("ERROR: Empty response from get_courses handler.")
        return False
    
    text_content = response[0]
    print(f"Course retrieval response: {text_content.text}")
    
    # Check if course retrieval was successful
    if "Error" in text_content.text:
        print("Course retrieval test FAILED! ❌")
        return False
    elif "Found" in text_content.text and "courses" in text_content.text:
        print("Course retrieval test SUCCESS! ✅")
        return True
    elif "No courses found" in text_content.text:
        print("No courses found, but API worked correctly.")
        print("Course retrieval test SUCCESS! ✅")
        return True
    else:
        print("Unexpected response from course retrieval.")
        print("Course retrieval test FAILED! ❌")
        return False

async def main():
    """Run all tests."""
    print("=== Starting eClass MCP Server Course Tests ===")
    
    logged_in = await ensure_login()
    
    if logged_in:
        await test_get_courses()
    
    print("=== Completed eClass MCP Server Course Tests ===")

if __name__ == "__main__":
    asyncio.run(main()) 