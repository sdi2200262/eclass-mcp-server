#!/usr/bin/env python3
"""
eClass Client - Authentication and Basic Functionality

This module provides a client for interacting with an eClass platform instance.
It handles authentication and session management for accessing eClass resources.
Specifically tailored for UoA's SSO authentication system.
"""

import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('eclass_client')

class EClassClient:
    """Client for interacting with an eClass platform instance through UoA's SSO."""
    
    def __init__(self, base_url=None):
        """
        Initialize the eClass client.
        
        Args:
            base_url (str, optional): The base URL of the eClass instance.
                If not provided, it will be loaded from the environment.
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize session and state
        self.session = requests.Session()
        self.logged_in = False
        
        # Set base URL
        self.base_url = base_url or os.getenv('ECLASS_URL')
        if not self.base_url:
            raise ValueError("eClass URL not provided and not found in environment")
        
        # Remove trailing slash if present
        self.base_url = self.base_url.rstrip('/')
        
        # Set SSO URLs
        self.login_form_url = f"{self.base_url}/main/login_form.php"
        
        logger.info(f"Initialized eClass client for {self.base_url}")
    
    def login(self, username=None, password=None):
        """
        Log in to eClass using username/password through UoA's SSO.
        
        Args:
            username (str, optional): eClass username. 
                If not provided, it will be loaded from the environment.
            password (str, optional): eClass password.
                If not provided, it will be loaded from the environment.
                
        Returns:
            bool: True if login was successful, False otherwise.
        """
        username = username or os.getenv('ECLASS_USERNAME')
        password = password or os.getenv('ECLASS_PASSWORD')
        
        if not username or not password:
            raise ValueError("Username and password must be provided or set in environment")
        
        logger.info(f"Attempting to log in as {username}")
        
        # Step 1: Visit the eClass login form page
        try:
            response = self.session.get(self.login_form_url)
            response.raise_for_status()
            logger.info("Accessed eClass login form")
        except requests.RequestException as e:
            logger.error(f"Failed to access login form: {e}")
            return False
        
        # Step 2: Find the SSO login button and follow it
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
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
                logger.error("Could not find SSO login link on the login page")
                return False
            
            # Make sure the URL is absolute
            if not sso_link.startswith(('http://', 'https://')):
                if sso_link.startswith('/'):
                    sso_link = f"{self.base_url}{sso_link}"
                else:
                    sso_link = f"{self.base_url}/{sso_link}"
            
            logger.info(f"Found SSO login link: {sso_link}")
            
            # Follow the SSO link
            response = self.session.get(sso_link)
            response.raise_for_status()
            logger.info("Redirected to SSO login page")
        except requests.RequestException as e:
            logger.error(f"Failed to access SSO page: {e}")
            return False
        except Exception as e:
            logger.error(f"Error parsing login page: {e}")
            return False
        
        # Step 3: Extract execution parameter and submit login form to CAS
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if we're already on the CAS login page
            if 'sso.uoa.gr' not in response.url:
                logger.error(f"Unexpected redirect to {response.url}")
                return False
            
            # Find execution value
            execution_input = soup.find('input', {'name': 'execution'})
            if not execution_input:
                logger.error("Could not find execution parameter on SSO page")
                return False
            
            execution = execution_input.get('value')
            
            # Find login form action
            form = soup.find('form', {'id': 'fm1'}) or soup.find('form')
            if not form:
                logger.error("Could not find login form on SSO page")
                return False
            
            action = form.get('action')
            if not action:
                # Use the current URL as fallback
                action = response.url
            elif not action.startswith(('http://', 'https://')):
                # Make the action URL absolute
                if action.startswith('/'):
                    action = f"https://sso.uoa.gr{action}"
                else:
                    action = f"https://sso.uoa.gr/{action}"
            
            # Prepare login data
            login_data = {
                'username': username,
                'password': password,
                'execution': execution,
                '_eventId': 'submit',
                'geolocation': ''
            }
            
            # Submit login form
            response = self.session.post(action, data=login_data)
            response.raise_for_status()
            
            # Check for authentication errors
            if 'Πόροι Πληροφορικής ΕΚΠΑ' not in response.text and 'The credentials you provided cannot be determined to be authentic' not in response.text:
                logger.info("Successfully authenticated with SSO")
            else:
                soup = BeautifulSoup(response.text, 'html.parser')
                error_msg = soup.find('div', {'id': 'msg'})
                if error_msg:
                    logger.error(f"SSO login error: {error_msg.text.strip()}")
                else:
                    logger.error("SSO login failed without specific error message")
                return False
            
        except requests.RequestException as e:
            logger.error(f"Failed during SSO authentication: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during SSO authentication: {e}")
            return False
        
        # Step 4: Check if we've been redirected to eClass and verify login success
        try:
            # We should now be redirected back to eClass
            if 'eclass.uoa.gr' in response.url:
                # Try to access portfolio page to verify login
                portfolio_url = f"{self.base_url}/main/portfolio.php"
                response = self.session.get(portfolio_url)
                response.raise_for_status()
                
                # Check if we can access the portfolio page
                if 'Μαθήματα' in response.text or 'portfolio' in response.text.lower() or 'course' in response.text.lower():
                    self.logged_in = True
                    logger.info("Login successful, redirected to eClass portfolio")
                    return True
                else:
                    logger.error("Could not access portfolio page after login")
                    return False
            else:
                logger.error(f"Unexpected redirect after login: {response.url}")
                return False
        except requests.RequestException as e:
            logger.error(f"Failed to verify login: {e}")
            return False
        except Exception as e:
            logger.error(f"Error verifying login: {e}")
            return False
    
    def get_courses(self):
        """
        Get list of enrolled courses.
        
        Returns:
            list: A list of dictionaries containing course information.
        """
        if not self.logged_in:
            logger.error("Not logged in")
            return []
        
        courses_url = f"{self.base_url}/main/portfolio.php"
        try:
            response = self.session.get(courses_url)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch courses: {e}")
            return []
        
        courses = []
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
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
                                'url': href if href.startswith('http') else f"{self.base_url}/{href.lstrip('/')}"
                            })
            else:
                for course_elem in course_elements:
                    course_link = course_elem.find('a') or course_elem
                    if course_link and course_link.get('href'):
                        course_name = course_link.text.strip()
                        course_url = course_link.get('href')
                        courses.append({
                            'name': course_name,
                            'url': course_url if course_url.startswith('http') else f"{self.base_url}/{course_url.lstrip('/')}"
                        })
        
        except Exception as e:
            logger.error(f"Failed to parse courses: {e}")
        
        logger.info(f"Found {len(courses)} courses")
        return courses
    
    def logout(self):
        """
        Log out from eClass.
        
        Returns:
            bool: True if logout was successful, False otherwise.
        """
        if not self.logged_in:
            logger.warning("Not logged in, nothing to do")
            return True
        
        logout_url = f"{self.base_url}/index.php?logout=yes"
        try:
            response = self.session.get(logout_url)
            response.raise_for_status()
            self.logged_in = False
            logger.info("Logged out successfully")
            return True
        except requests.RequestException as e:
            logger.error(f"Logout failed: {e}")
            return False


def main():
    """Main function to demonstrate eClass client usage."""
    try:
        # Create client instance
        client = EClassClient()
        
        # Attempt to login
        if client.login():
            print("Login successful!")
            
            # Get courses
            courses = client.get_courses()
            print(f"Found {len(courses)} courses:")
            for i, course in enumerate(courses, 1):
                print(f"{i}. {course['name']}")
            
            # Logout
            client.logout()
        else:
            print("Login failed. Please check your credentials.")
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main() 