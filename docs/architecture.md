# System Architecture

This document describes the architecture and design of the eClass MCP Server.

## System Overview

The server follows a modular architecture separating the MCP protocol handling from the business logic of interacting with the eClass platform.

```
server.py                       # Core MCP server setup, tool registration, and request handling
├── authentication.py           # Authentication with eClass and SSO system
├── course_management.py        # Course-related functionality
└── html_parsing.py             # HTML parsing utilities
```

### Components

*   **`server.py`**: The entry point. It initializes the MCP server, registers tool handlers, and manages the global `SessionState`.
*   **`authentication.py`**: Handles the complex SSO login flow, logout, and session verification.
*   **`course_management.py`**: Logic for retrieving and formatting course lists.
*   **`html_parsing.py`**: Uses `BeautifulSoup` to extract data (SSO links, execution tokens, course lists) from eClass HTML responses.

## Session Management

The server maintains state between MCP tool calls using a global `SessionState` class.

### `SessionState` Class

*   **Persistence**: Wraps a `requests.Session()` object which automatically handles cookie persistence (specifically `PHPSESSID`) across HTTP requests.
*   **State Tracking**: Maintains flags for `logged_in` status and stores the current `username` and `courses`.
*   **Validation**: The `is_session_valid()` method proactively checks if the session is still active by attempting to access a protected resource (`portfolio.php`). If a redirect to the login page is detected, the session is marked as invalid.

## Authentication Flow

The server implements a specific scraping-based authentication flow to handle UoA's CAS SSO system.

1.  **Initial Request**: The server visits the eClass login form (`/main/login_form.php`).
2.  **SSO Discovery**: It parses the HTML to find the "Login with UoA Account" link (typically pointing to `/modules/auth/cas.php`).
3.  **CAS Redirection**: Following the link redirects to the SSO provider (`sso.uoa.gr`).
4.  **Form Extraction**: The server parses the CAS login page to extract the hidden `execution` token and the form `action` URL.
5.  **Credential Submission**: It POSTs the username, password, and execution token to the CAS server.
6.  **Verification**: Upon success, the server follows the redirect back to eClass and verifies access to the portfolio page.

## Configuration

Configuration is handled via environment variables loaded from a `.env` file:
*   `ECLASS_URL`: The base URL of the eClass instance (optional, defaults to `https://eclass.uoa.gr`).
*   `ECLASS_SSO_DOMAIN`: The domain of the SSO server (optional, defaults to `sso.uoa.gr`). Only change this if using a different eClass instance with a different SSO provider.
*   `ECLASS_USERNAME`: User credentials.
*   `ECLASS_PASSWORD`: User credentials.

**Note:** Only the UoA eClass instance is currently supported and tested.
