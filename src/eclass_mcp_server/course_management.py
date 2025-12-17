"""
Course management module for eClass MCP Server.

Handles retrieval and formatting of course information from eClass.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import mcp.types as types
import requests

from . import html_parsing

if TYPE_CHECKING:
    from .server import SessionState

logger = logging.getLogger('eclass_mcp_server.course_management')


def get_courses(
    session_state: SessionState
) -> Tuple[bool, Optional[str], Optional[List[Dict[str, str]]]]:
    """
    Retrieve a list of enrolled courses from eClass.
    
    Returns:
        Tuple of (success, message, courses).
        On success: (True, None, courses_list)
        On empty result: (True, message, [])
        On failure: (False, error_message, None)
    """
    if not session_state.logged_in:
        return False, "Not logged in. Please log in first using the login tool.", None
    
    if not session_state.is_session_valid():
        return False, "Session expired. Please log in again.", None
    
    try:
        response = session_state.session.get(session_state.portfolio_url)
        response.raise_for_status()
        
        courses = html_parsing.extract_courses(response.text, session_state.base_url)
        session_state.courses = courses
        
        if not courses:
            return True, "No courses found. You may not be enrolled in any courses.", []
        
        logger.info(f"Successfully retrieved {len(courses)} courses")
        return True, None, courses
    
    except requests.RequestException as e:
        logger.error(f"Network error getting courses: {e}")
        return False, f"Network error retrieving courses: {e}", None
    except Exception as e:
        logger.error(f"Error getting courses: {e}")
        return False, f"Error retrieving courses: {e}", None


def format_courses_response(
    success: bool, message: Optional[str], courses: Optional[List[Dict[str, str]]]
) -> types.TextContent:
    """Format course list response for MCP."""
    if not success:
        return types.TextContent(
            type="text",
            text=f"Error: {message}",
        )
    
    if message:  # No courses found message
        return types.TextContent(
            type="text",
            text=message,
        )
    
    course_list = html_parsing.format_course_list(courses)
    return types.TextContent(
        type="text",
        text=f"Found {len(courses)} courses:\n\n{course_list}",
    )
