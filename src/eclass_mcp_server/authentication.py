"""
Authentication module for eClass MCP Server.

Handles authentication with eClass through UoA's SSO (CAS) system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Tuple
from urllib.parse import urlparse

import mcp.types as types
import requests

from . import html_parsing

if TYPE_CHECKING:
    from .server import SessionState

logger = logging.getLogger('eclass_mcp_server.authentication')


def attempt_login(
    session_state: SessionState, username: str, password: str
) -> Tuple[bool, Optional[str]]:
    """
    Attempt to log in to eClass using the SSO authentication flow.
    
    Returns:
        Tuple of (success, error_message). On success, error_message is None.
    """
    try:
        # Step 1: Visit the eClass login form page
        response = session_state.session.get(session_state.login_form_url)
        response.raise_for_status()
        
        # Step 2: Find and follow the SSO login link
        sso_link = html_parsing.extract_sso_link(response.text, session_state.base_url)
        if not sso_link:
            return False, "Could not find SSO login link on the login page"
        
        response = session_state.session.get(sso_link)
        response.raise_for_status()
        
        # Step 3: Validate SSO redirect and extract CAS form data
        if not _is_valid_sso_redirect(response.url, session_state):
            return False, f"Unexpected redirect to {response.url}"
        
        execution, action, error_text = html_parsing.extract_cas_form_data(
            response.text, response.url, session_state.sso_base_url
        )
        
        if error_text and ('authenticate' in error_text.lower() or 'credentials' in error_text.lower()):
            return False, f"Authentication error: {error_text}"
        if not execution:
            return False, "Could not find execution parameter on SSO page"
        if not action:
            return False, "Could not find login form on SSO page"
        
        # Step 4: Submit credentials to CAS
        login_data = {
            'username': username,
            'password': password,
            'execution': execution,
            '_eventId': 'submit',
            'geolocation': ''
        }
        
        response = session_state.session.post(action, data=login_data)
        response.raise_for_status()
        
        # Check for authentication errors in response
        if 'Πόροι Πληροφορικής ΕΚΠΑ' in response.text or \
           'The credentials you provided cannot be determined to be authentic' in response.text:
            _, _, error_text = html_parsing.extract_cas_form_data(response.text, response.url)
            if error_text:
                return False, f"Authentication error: {error_text}"
            return False, "Authentication failed: Invalid credentials"
        
        logger.info("Successfully authenticated with SSO")
        
        # Step 5: Verify login by accessing portfolio page
        if session_state.eclass_domain not in response.url:
            return False, f"Unexpected redirect after login: {response.url}"
        
        response = session_state.session.get(session_state.portfolio_url)
        response.raise_for_status()
        
        if not html_parsing.verify_login_success(response.text):
            return False, "Could not access portfolio page after login"
        
        session_state.logged_in = True
        session_state.username = username
        logger.info("Login successful, redirected to eClass portfolio")
        return True, None
    
    except requests.RequestException as e:
        logger.error(f"Request error during login: {e}")
        return False, f"Network error during login process: {e}"
    except Exception as e:
        logger.error(f"Login error: {e}")
        return False, f"Error during login process: {e}"


def _is_valid_sso_redirect(response_url: str, session_state: SessionState) -> bool:
    """Check if the redirect is to a valid SSO domain."""
    response_url_domain = urlparse(response_url).netloc
    sso_domain_netloc = urlparse(session_state.sso_base_url).netloc
    
    # Valid if: SSO domain in URL, exact domain match, or same domain for local testing
    return (
        session_state.sso_domain in response_url or
        response_url_domain == sso_domain_netloc or
        (session_state.eclass_domain == session_state.sso_domain and
         session_state.eclass_domain in response_url)
    )


def perform_logout(session_state: SessionState) -> Tuple[bool, Optional[str]]:
    """
    Log out from eClass.
    
    Returns:
        Tuple of (success, username_or_error).
        On success with prior login: (True, username)
        On success without prior login: (True, None)
        On failure: (False, error_message)
    """
    if not session_state.logged_in:
        return True, None
    
    try:
        response = session_state.session.get(session_state.logout_url)
        response.raise_for_status()
        
        username = session_state.username
        session_state.reset()
        return True, username
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return False, f"Error during logout: {e}"


def format_login_response(
    success: bool, message: Optional[str], username: Optional[str] = None
) -> types.TextContent:
    """Format login response for MCP."""
    if success:
        return types.TextContent(
            type="text",
            text=f"Login successful! You are now logged in as {username}.",
        )
    return types.TextContent(
        type="text",
        text=f"Error: {message}",
    )


def format_logout_response(
    success: bool, username_or_error: Optional[str]
) -> types.TextContent:
    """Format logout response for MCP."""
    if success:
        if username_or_error:
            return types.TextContent(
                type="text",
                text=f"Successfully logged out user {username_or_error}.",
            )
        return types.TextContent(
            type="text",
            text="Not logged in, nothing to do.",
        )
    return types.TextContent(
        type="text",
        text=f"Error during logout: {username_or_error}",
    )


def format_authstatus_response(session_state: SessionState) -> types.TextContent:
    """Format authentication status response for MCP."""
    if not session_state.logged_in:
        return types.TextContent(
            type="text",
            text="Status: Not logged in",
        )
    
    if session_state.is_session_valid():
        return types.TextContent(
            type="text",
            text=f"Status: Logged in as {session_state.username}\nCourses: {len(session_state.courses)} enrolled",
        )
    
    return types.TextContent(
        type="text",
        text="Status: Session expired. Please log in again.",
    )
