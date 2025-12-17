#!/usr/bin/env python3
"""
eClass Client - Standalone client for eClass platform.

This module provides a standalone client for interacting with eClass without MCP.
It demonstrates the server's core functionality in a simple sequential script,
reusing the authentication and HTML parsing modules from the MCP server.

This client serves as:
1. A reference implementation showing how eClass authentication works
2. A simpler alternative for projects that don't require MCP integration
3. A demonstration of the modular architecture

Usage:
    python eclass_client.py
"""

import logging
import os
import sys
from typing import Dict, List
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# Add src directory to path for module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eclass_mcp_server import authentication, html_parsing

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('eclass_client')


class EClassClient:
    """Standalone client for eClass platform using shared modules."""
    
    def __init__(self, base_url: str | None = None) -> None:
        """
        Initialize the eClass client.
        
        Args:
            base_url: Base URL of the eClass instance. Defaults to env or UoA.
        """
        load_dotenv()
        
        self.session = requests.Session()
        self.logged_in = False
        
        # Configuration mirrors server.SessionState
        self.base_url = (base_url or os.getenv('ECLASS_URL', 'https://eclass.uoa.gr')).rstrip('/')
        self.eclass_domain = urlparse(self.base_url).netloc
        
        self.sso_domain = os.getenv('ECLASS_SSO_DOMAIN', 'sso.uoa.gr')
        sso_protocol = os.getenv('ECLASS_SSO_PROTOCOL', 'https')
        self.sso_base_url = f"{sso_protocol}://{self.sso_domain}"
        
        self.login_form_url = f"{self.base_url}/main/login_form.php"
        self.portfolio_url = f"{self.base_url}/main/portfolio.php"
        self.logout_url = f"{self.base_url}/index.php?logout=yes"
        
        self.username: str | None = None
        self.courses: List[Dict[str, str]] = []
        
        logger.info(f"Initialized eClass client for {self.base_url} (SSO: {self.sso_domain})")
    
    def login(self, username: str | None = None, password: str | None = None) -> bool:
        """
        Log in to eClass using SSO authentication.
        
        Args:
            username: eClass username. Defaults to env.
            password: eClass password. Defaults to env.
            
        Returns:
            True if login was successful.
        """
        username = username or os.getenv('ECLASS_USERNAME')
        password = password or os.getenv('ECLASS_PASSWORD')
        
        if not username or not password:
            raise ValueError("Username and password must be provided or set in environment")
        
        logger.info(f"Attempting to log in as {username}")
        
        # Use authentication module's login flow
        success, error = authentication.attempt_login(self, username, password)
        
        if success:
            logger.info("Login successful")
            return True
        
        logger.error(f"Login failed: {error}")
        return False
    
    def get_courses(self) -> List[Dict[str, str]]:
        """
        Get list of enrolled courses.
        
        Returns:
            List of course dicts with 'name' and 'url' keys.
        """
        if not self.logged_in:
            logger.error("Not logged in")
            return []
        
        try:
            response = self.session.get(self.portfolio_url)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch courses: {e}")
            return []
        
        # Use html_parsing module
        self.courses = html_parsing.extract_courses(response.text, self.base_url)
        logger.info(f"Found {len(self.courses)} courses")
        return self.courses
    
    def logout(self) -> bool:
        """
        Log out from eClass.
        
        Returns:
            True if logout was successful.
        """
        if not self.logged_in:
            logger.warning("Not logged in, nothing to do")
            return True
        
        try:
            response = self.session.get(self.logout_url)
            response.raise_for_status()
            self.reset()
            logger.info("Logged out successfully")
            return True
        except requests.RequestException as e:
            logger.error(f"Logout failed: {e}")
            return False
    
    def reset(self) -> None:
        """Reset the client state."""
        self.session = requests.Session()
        self.logged_in = False
        self.username = None
        self.courses = []


def main() -> None:
    """Demonstrate eClass client usage."""
    try:
        client = EClassClient()
        
        if client.login():
            print("Login successful!")
            
            courses = client.get_courses()
            print(f"\nFound {len(courses)} courses:")
            for i, course in enumerate(courses, 1):
                print(f"{i}. {course['name']}")
                print(f"   URL: {course['url']}")
            
            client.logout()
            print("\nLogged out.")
        else:
            print("Login failed. Please check your credentials.")
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
