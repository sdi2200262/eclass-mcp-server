"""
Course Management Module for eClass MCP Server

This module handles operations related to retrieving and processing course information
from the eClass platform.
"""

import logging
from typing import List, Dict, Optional, Tuple

import requests
import mcp.types as types

from . import html_parsing

# Configure logging
logger = logging.getLogger('eclass_mcp_server.course_management')

def get_courses(session_state) -> Tuple[bool, Optional[str], Optional[List[Dict[str, str]]]]:
    """
    Retrieve a list of enrolled courses from eClass.
    
    Args:
        session_state: The current session state
        
    Returns:
        Tuple of (success, error_message, courses)
        If successful, error_message will be None and courses will contain the list
        If unsuccessful, error_message will contain the error and courses will be None
    """
    if not session_state.logged_in:
        return False, "Not logged in. Please log in first using the login tool.", None
    
    # Check if session is still valid
    if not session_state.is_session_valid():
        return False, "Session expired. Please log in again.", None
    
    try:
        response = session_state.session.get(session_state.portfolio_url)
        response.raise_for_status()
        
        # Parse courses from the HTML response
        courses = html_parsing.extract_courses(response.text, session_state.base_url)
        
        # Store courses in session for future use
        session_state.courses = courses
        
        if not courses:
            return True, "No courses found. You may not be enrolled in any courses.", []
        
        logger.info(f"Successfully retrieved {len(courses)} courses")
        return True, None, courses
    
    except requests.RequestException as e:
        logger.error(f"Network error getting courses: {str(e)}")
        return False, f"Network error retrieving courses: {str(e)}", None
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}")
        return False, f"Error retrieving courses: {str(e)}", None

def format_courses_response(success: bool, message: Optional[str], courses: Optional[List[Dict[str, str]]]) -> types.TextContent:
    """
    Format course list response for MCP.
    
    Args:
        success: Whether course retrieval was successful
        message: Optional message (error message or "no courses" message)
        courses: List of courses if successful
        
    Returns:
        Formatted MCP TextContent response
    """
    if not success:
        return types.TextContent(
            type="text",
            text=f"Error: {message}",
        )
    
    if message:  # No courses found
        return types.TextContent(
            type="text",
            text=message,
        )
    
    # Format course list
    course_list = html_parsing.format_course_list(courses)
    return types.TextContent(
        type="text",
        text=f"Found {len(courses)} courses:\n\n{course_list}",
    ) 