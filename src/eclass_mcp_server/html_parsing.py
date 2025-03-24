"""
HTML Parsing Module for eClass MCP Server

This module contains functions for parsing HTML content from eClass pages
using BeautifulSoup. It extracts various elements such as SSO links,
form parameters, and course information.
"""

import logging
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger('eclass_mcp_server.html_parsing')

def extract_sso_link(html_content: str, base_url: str) -> Optional[str]:
    """
    Extract the SSO login link from the eClass login page.
    
    Args:
        html_content: HTML content of the login page
        base_url: Base URL of the eClass instance
        
    Returns:
        The SSO login URL or None if not found
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    sso_link = None
    
    # Look for the UoA login button (it could be a button or a link)
    for link in soup.find_all('a'):
        if 'Είσοδος με λογαριασμό ΕΚΠΑ' in link.text or 'ΕΚΠΑ' in link.text:
            sso_link = link.get('href')
            break
    
    if not sso_link:
        # Try alternate method to find the SSO link
        for form in soup.find_all('form'):
            if form.get('action') and 'cas.php' in form.get('action'):
                sso_link = form.get('action')
                break
    
    if not sso_link:
        logger.warning("Could not find SSO login link on the login page")
        return None
    
    # Make sure the URL is absolute
    if not sso_link.startswith(('http://', 'https://')):
        if sso_link.startswith('/'):
            sso_link = f"{base_url}{sso_link}"
        else:
            sso_link = f"{base_url}/{sso_link}"
    
    logger.debug(f"Extracted SSO link: {sso_link}")
    return sso_link

def extract_cas_form_data(html_content: str, current_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract execution parameter and form action from CAS login page.
    
    Args:
        html_content: HTML content of the CAS login page
        current_url: Current URL of the page (used as fallback for form action)
        
    Returns:
        Tuple of (execution_value, form_action, error_message)
        If extraction fails, appropriate values will be None
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check if we're on the error page
    error_msg = soup.find('div', {'id': 'msg'})
    error_text = error_msg.text.strip() if error_msg else None
    
    # Find execution value
    execution_input = soup.find('input', {'name': 'execution'})
    if not execution_input:
        logger.warning("Could not find execution parameter on SSO page")
        return None, None, error_text or "Could not find execution parameter on SSO page"
    
    execution = execution_input.get('value')
    
    # Find login form action
    form = soup.find('form', {'id': 'fm1'}) or soup.find('form')
    if not form:
        logger.warning("Could not find login form on SSO page")
        return execution, None, error_text or "Could not find login form on SSO page"
    
    action = form.get('action')
    if not action:
        # Use the current URL as fallback
        action = current_url
    elif not action.startswith(('http://', 'https://')):
        # Make the action URL absolute
        if action.startswith('/'):
            action = f"https://sso.uoa.gr{action}"
        else:
            action = f"https://sso.uoa.gr/{action}"
    
    return execution, action, error_text

def verify_login_success(html_content: str) -> bool:
    """
    Verify if login was successful by checking for expected content on the portfolio page.
    
    Args:
        html_content: HTML content of the portfolio page
        
    Returns:
        True if login was successful, False otherwise
    """
    return ('Μαθήματα' in html_content or 
            'portfolio' in html_content.lower() or 
            'course' in html_content.lower())

def extract_courses(html_content: str, base_url: str) -> List[Dict[str, str]]:
    """
    Extract course information from the portfolio page.
    
    Args:
        html_content: HTML content of the portfolio page
        base_url: Base URL of the eClass instance
        
    Returns:
        List of courses with name and URL
    """
    courses = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try different CSS selectors that might contain course information
    course_elements = (
        soup.select('.course-title') or
        soup.select('.lesson-title') or
        soup.select('.course-box .title') or
        soup.select('.course-info h4')
    )
    
    if not course_elements:
        # Try to find course links using a more general approach
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'courses' in href or 'course.php' in href:
                course_name = link.text.strip()
                if course_name:  # Only include if there's a name
                    courses.append({
                        'name': course_name,
                        'url': href if href.startswith('http') else f"{base_url}/{href.lstrip('/')}"
                    })
    else:
        for course_elem in course_elements:
            course_link = course_elem.find('a') or course_elem
            if course_link and course_link.get('href'):
                course_name = course_link.text.strip()
                course_url = course_link.get('href')
                courses.append({
                    'name': course_name,
                    'url': course_url if course_url.startswith('http') else f"{base_url}/{course_url.lstrip('/')}"
                })
    
    logger.debug(f"Extracted {len(courses)} courses")
    return courses

def format_course_list(courses: List[Dict[str, str]]) -> str:
    """
    Format course list for display.
    
    Args:
        courses: List of courses with name and URL
        
    Returns:
        Formatted string with course list
    """
    return "\n".join([f"{i+1}. {course['name']}" for i, course in enumerate(courses)]) 