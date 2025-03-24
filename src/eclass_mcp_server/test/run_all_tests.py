"""
Run all tests for the eClass MCP Server.

This script runs all the tests for the eClass MCP Server in sequence.
It tests login, course retrieval, and logout functionality.
"""

import asyncio
import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from eclass_mcp_server.server import session_state, handle_login, handle_get_courses, handle_logout, handle_authstatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_all_tests')

# Test results tracking
test_results = {
    'login': False,
    'authstatus_after_login': False,
    'get_courses': False,
    'logout': False,
    'authstatus_after_logout': False
}

async def test_login():
    """Test the login functionality."""
    print("\n=== Testing Login ===")
    
    # Load environment variables
    load_dotenv()
    
    # Check if credentials are set
    username = os.getenv('ECLASS_USERNAME')
    password = os.getenv('ECLASS_PASSWORD')
    
    if not username or not password:
        print("ERROR: ECLASS_USERNAME and ECLASS_PASSWORD must be set in the .env file.")
        return False
    
    # Attempt login
    print("Attempting login...")
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

async def test_authstatus():
    """Test the authentication status functionality."""
    print("\n=== Testing Auth Status ===")
    
    # Get authentication status
    print("Checking authentication status...")
    response = await handle_authstatus()
    
    # Check response
    if not response or len(response) == 0:
        print("ERROR: Empty response from authstatus handler.")
        return False
    
    text_content = response[0]
    print(f"Auth status response: {text_content.text}")
    
    # Check status
    if "Status: Logged in as" in text_content.text:
        print("Auth status (logged in) test SUCCESS! ✅")
        return True
    elif "Status: Not logged in" in text_content.text and not session_state.logged_in:
        print("Auth status (not logged in) test SUCCESS! ✅")
        return True
    elif "Status: Session expired" in text_content.text and not session_state.is_session_valid():
        print("Auth status (session expired) test SUCCESS! ✅")
        return True
    else:
        print("Auth status test FAILED! ❌")
        return False

async def test_get_courses():
    """Test the course retrieval functionality."""
    print("\n=== Testing Course Retrieval ===")
    
    if not session_state.logged_in:
        print("Not logged in, skipping course retrieval test.")
        return False
    
    # Attempt to get courses
    print("Retrieving courses...")
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

async def test_logout():
    """Test the logout functionality."""
    print("\n=== Testing Logout ===")
    
    if not session_state.logged_in:
        print("Not logged in, skipping logout test.")
        return False
    
    # Attempt logout
    print("Attempting logout...")
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

async def run_all_tests():
    """Run all tests in sequence."""
    print("\n====== Starting All eClass MCP Server Tests ======\n")
    
    # Test login
    test_results['login'] = await test_login()
    
    # Test authentication status after login
    if test_results['login']:
        test_results['authstatus_after_login'] = await test_authstatus()
    
    # Test course retrieval
    if test_results['login']:
        test_results['get_courses'] = await test_get_courses()
    
    # Test logout
    if test_results['login']:
        test_results['logout'] = await test_logout()
    
    # Test authentication status after logout
    test_results['authstatus_after_logout'] = await test_authstatus()
    
    # Print summary
    print("\n====== Test Results Summary ======")
    for test_name, result in test_results.items():
        status = "PASSED ✅" if result else "FAILED ❌"
        print(f"{test_name}: {status}")
    
    # Overall result
    if all(test_results.values()):
        print("\nAll tests PASSED! ✅")
    else:
        print("\nSome tests FAILED! ❌")
    
    print("\n====== Completed All eClass MCP Server Tests ======\n")

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 