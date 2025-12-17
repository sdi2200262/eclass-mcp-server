"""
HTML parsing utilities for eClass MCP Server.

Uses BeautifulSoup to extract data from eClass and CAS SSO HTML responses.
"""

import logging
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

logger = logging.getLogger('eclass_mcp_server.html_parsing')


def extract_sso_link(html_content: str, base_url: str) -> Optional[str]:
    """
    Extract the SSO login link from the eClass login page.
    
    Returns:
        Absolute SSO login URL, or None if not found.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    sso_link = None
    
    # Look for UoA login button
    for link in soup.find_all('a'):
        if 'Είσοδος με λογαριασμό ΕΚΠΑ' in link.text or 'ΕΚΠΑ' in link.text:
            sso_link = link.get('href')
            break
    
    # Fallback: look for CAS form action
    if not sso_link:
        for form in soup.find_all('form'):
            if form.get('action') and 'cas.php' in form.get('action'):
                sso_link = form.get('action')
                break
    
    if not sso_link:
        logger.warning("Could not find SSO login link on the login page")
        return None
    
    # Ensure URL is absolute
    if not sso_link.startswith(('http://', 'https://')):
        sso_link = f"{base_url}/{sso_link.lstrip('/')}"
    
    logger.debug(f"Extracted SSO link: {sso_link}")
    return sso_link


def extract_cas_form_data(
    html_content: str,
    current_url: str,
    sso_base_url: str = "https://sso.uoa.gr"
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract execution parameter and form action from CAS login page.
    
    Returns:
        Tuple of (execution_value, form_action, error_message).
        On parsing failure, appropriate values will be None.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check for error message
    error_msg = soup.find('div', {'id': 'msg'})
    error_text = error_msg.text.strip() if error_msg else None
    
    # Find execution token
    execution_input = soup.find('input', {'name': 'execution'})
    if not execution_input:
        logger.warning("Could not find execution parameter on SSO page")
        return None, None, error_text or "Could not find execution parameter on SSO page"
    
    execution = execution_input.get('value')
    
    # Find login form
    form = soup.find('form', {'id': 'fm1'}) or soup.find('form')
    if not form:
        logger.warning("Could not find login form on SSO page")
        return execution, None, error_text or "Could not find login form on SSO page"
    
    action = form.get('action')
    if not action:
        action = current_url
    elif not action.startswith(('http://', 'https://')):
        action = f"{sso_base_url}/{action.lstrip('/')}"
    
    return execution, action, error_text


def verify_login_success(html_content: str) -> bool:
    """
    Verify if login was successful by checking for portfolio page content.
    """
    return ('Μαθήματα' in html_content or
            'portfolio' in html_content.lower() or
            'course' in html_content.lower())


def extract_courses(html_content: str, base_url: str) -> List[Dict[str, str]]:
    """
    Extract course information from the portfolio page.
    
    Returns:
        List of dicts with 'name' and 'url' keys.
    """
    courses = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Try specific course selectors
    course_elements = (
        soup.select('.course-title') or
        soup.select('.lesson-title') or
        soup.select('.course-box .title') or
        soup.select('.course-info h4')
    )
    
    if course_elements:
        for course_elem in course_elements:
            course_link = course_elem.find('a') or course_elem
            if course_link and course_link.get('href'):
                course_name = course_link.text.strip()
                course_url = course_link.get('href')
                if course_name:
                    courses.append({
                        'name': course_name,
                        'url': _make_absolute_url(course_url, base_url)
                    })
    else:
        # Fallback: find course links by URL pattern
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if 'courses' in href or 'course.php' in href:
                course_name = link.text.strip()
                if course_name:
                    courses.append({
                        'name': course_name,
                        'url': _make_absolute_url(href, base_url)
                    })
    
    logger.debug(f"Extracted {len(courses)} courses")
    return courses


def _make_absolute_url(url: str, base_url: str) -> str:
    """Convert relative URL to absolute URL."""
    if url.startswith(('http://', 'https://')):
        return url
    return f"{base_url}/{url.lstrip('/')}"


def format_course_list(courses: List[Dict[str, str]]) -> str:
    """
    Format course list for display.
    
    Returns:
        Formatted string with numbered courses and URLs.
    """
    lines = []
    for i, course in enumerate(courses, 1):
        lines.append(f"{i}. {course['name']}")
        lines.append(f"   URL: {course['url']}")
    return "\n".join(lines)
