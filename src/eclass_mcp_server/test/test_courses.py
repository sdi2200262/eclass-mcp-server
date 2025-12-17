"""Test course retrieval functionality for eClass MCP Server."""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from eclass_mcp_server.server import handle_get_courses, handle_login, session_state

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_courses')


async def ensure_login() -> bool:
    """Ensure logged in before testing course retrieval."""
    if session_state.logged_in and session_state.is_session_valid():
        print("Already logged in, proceeding with tests.")
        return True
    
    print("Not logged in, attempting login...")
    
    load_dotenv()
    
    username = os.getenv('ECLASS_USERNAME')
    password = os.getenv('ECLASS_PASSWORD')
    
    if not username or not password:
        print("ERROR: ECLASS_USERNAME and ECLASS_PASSWORD must be set in the .env file.")
        return False
    
    response = await handle_login()
    
    if response and "Login successful" in response[0].text:
        print("Login successful, proceeding with tests.")
        return True
    
    print("Login failed, cannot proceed with course tests.")
    return False


async def test_get_courses() -> bool:
    """Test the course retrieval functionality."""
    print("Testing course retrieval functionality...")
    
    response = await handle_get_courses()
    
    if not response:
        print("ERROR: Empty response from get_courses handler.")
        return False
    
    text_content = response[0]
    print(f"Course retrieval response: {text_content.text}")
    
    if "Error" in text_content.text:
        print("Course retrieval test FAILED!")
        return False
    
    if "No courses found" in text_content.text:
        print("No courses found, but API worked correctly.")
        print("Course retrieval test SUCCESS!")
        return True
    
    if "Found" in text_content.text and "courses" in text_content.text:
        if "URL:" in text_content.text:
            print("Course retrieval test SUCCESS!")
            return True
        print("Course retrieval test FAILED! Output format is incorrect (missing URLs).")
        return False
    
    print("Unexpected response from course retrieval.")
    print("Course retrieval test FAILED!")
    return False


async def main() -> None:
    """Run course tests."""
    print("=== Starting eClass MCP Server Course Tests ===")
    
    if await ensure_login():
        await test_get_courses()
    
    print("=== Completed eClass MCP Server Course Tests ===")


if __name__ == "__main__":
    asyncio.run(main())
