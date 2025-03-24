"""
Authentication Module for eClass MCP Server

This module handles authentication with the eClass platform through UoA's SSO system.
It includes functions for logging in, verifying login success, and logging out.
"""

import logging
import requests
from typing import Dict, Tuple, Optional

import mcp.types as types

from . import html_parsing

# Configure logging
logger = logging.getLogger('eclass_mcp_server.authentication')

def attempt_login(session_state, username: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Attempt to log in to eClass using the SSO authentication flow.
    
    Args:
        session_state: The current session state
        username: eClass username
        password: eClass password
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Step 1: Visit the eClass login form page
        response = session_state.session.get(session_state.login_form_url)
        response.raise_for_status()
        
        # Step 2: Find the SSO login button and follow it
        sso_link = html_parsing.extract_sso_link(response.text, session_state.base_url)
        if not sso_link:
            return False, "Could not find SSO login link on the login page"
        
        # Follow the SSO link
        response = session_state.session.get(sso_link)
        response.raise_for_status()
        
        # Step 3: Extract execution parameter and submit login form to CAS
        if 'sso.uoa.gr' not in response.url:
            return False, f"Unexpected redirect to {response.url}"
        
        execution, action, error_text = html_parsing.extract_cas_form_data(response.text, response.url)
        
        # Handle extraction errors
        if error_text and ('authenticate' in error_text.lower() or 'credentials' in error_text.lower()):
            return False, f"Authentication error: {error_text}"
            
        if not execution:
            return False, "Could not find execution parameter on SSO page"
            
        if not action:
            return False, "Could not find login form on SSO page"
        
        # Prepare login data
        login_data = {
            'username': username,
            'password': password,
            'execution': execution,
            '_eventId': 'submit',
            'geolocation': ''
        }
        
        # Submit login form
        response = session_state.session.post(action, data=login_data)
        response.raise_for_status()
        
        # Check for authentication errors
        if 'Πόροι Πληροφορικής ΕΚΠΑ' not in response.text and 'The credentials you provided cannot be determined to be authentic' not in response.text:
            logger.info("Successfully authenticated with SSO")
        else:
            # Re-parse to get error message if present
            execution, action, error_text = html_parsing.extract_cas_form_data(response.text, response.url)
            if error_text:
                return False, f"Authentication error: {error_text}"
            else:
                return False, "Authentication failed: Invalid credentials"
        
        # Step 4: Check if we've been redirected to eClass and verify login success
        if 'eclass.uoa.gr' in response.url:
            # Try to access portfolio page to verify login
            response = session_state.session.get(session_state.portfolio_url)
            response.raise_for_status()
            
            # Check if we can access the portfolio page
            if html_parsing.verify_login_success(response.text):
                session_state.logged_in = True
                session_state.username = username
                logger.info("Login successful, redirected to eClass portfolio")
                return True, None
            else:
                return False, "Could not access portfolio page after login"
        else:
            return False, f"Unexpected redirect after login: {response.url}"
    
    except requests.RequestException as e:
        logger.error(f"Request error during login: {str(e)}")
        return False, f"Network error during login process: {str(e)}"
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return False, f"Error during login process: {str(e)}"

def perform_logout(session_state) -> Tuple[bool, Optional[str]]:
    """
    Log out from eClass.
    
    Args:
        session_state: The current session state
        
    Returns:
        Tuple of (success, error_message or username)
    """
    if not session_state.logged_in:
        return True, None  # Already logged out
    
    try:
        response = session_state.session.get(session_state.logout_url)
        response.raise_for_status()
        
        # Store username for response message
        username = session_state.username
        
        # Reset session state
        session_state.reset()
        
        return True, username
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return False, f"Error during logout: {str(e)}"

def format_login_response(success: bool, message: Optional[str], username: Optional[str] = None) -> types.TextContent:
    """
    Format login response for MCP.
    
    Args:
        success: Whether login was successful
        message: Error message if login failed
        username: Username if login succeeded
        
    Returns:
        Formatted MCP TextContent response
    """
    if success:
        return types.TextContent(
            type="text",
            text=f"Login successful! You are now logged in as {username}.",
        )
    else:
        return types.TextContent(
            type="text",
            text=f"Error: {message}",
        )

def format_logout_response(success: bool, username_or_error: Optional[str]) -> types.TextContent:
    """
    Format logout response for MCP.
    
    Args:
        success: Whether logout was successful
        username_or_error: Username if logout succeeded, error message if failed
        
    Returns:
        Formatted MCP TextContent response
    """
    if success:
        if username_or_error:  # If we had a username
            return types.TextContent(
                type="text",
                text=f"Successfully logged out user {username_or_error}.",
            )
        else:
            return types.TextContent(
                type="text",
                text="Not logged in, nothing to do.",
            )
    else:
        return types.TextContent(
            type="text",
            text=f"Error during logout: {username_or_error}",
        )

def format_authstatus_response(session_state) -> types.TextContent:
    """
    Format authentication status response.
    
    Args:
        session_state: The current session state
        
    Returns:
        Formatted MCP TextContent response
    """
    if not session_state.logged_in:
        return types.TextContent(
            type="text",
            text="Status: Not logged in",
        )
    
    # Check if session is still valid
    is_valid = session_state.is_session_valid()
    
    if is_valid:
        return types.TextContent(
            type="text",
            text=f"Status: Logged in as {session_state.username}\nCourses: {len(session_state.courses)} enrolled",
        )
    else:
        return types.TextContent(
            type="text",
            text="Status: Session expired. Please log in again.",
        ) 