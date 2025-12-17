# System Architecture

This document describes the architecture and design of the eClass MCP Server.

## Overview

The server follows a modular architecture separating MCP protocol handling from eClass interaction logic.

```
src/eclass_mcp_server/
├── server.py               # MCP server, tool registration, SessionState
├── authentication.py       # SSO login flow, logout, session verification
├── course_management.py    # Course retrieval and formatting
└── html_parsing.py         # BeautifulSoup parsing utilities
```

## Components

### `server.py`

The main entry point containing:
- **`SessionState`**: Global class maintaining authentication state and `requests.Session`
- **Tool handlers**: `handle_login()`, `handle_get_courses()`, `handle_logout()`, `handle_authstatus()`
- **MCP server setup**: Tool registration via `@server.list_tools()` and `@server.call_tool()`

### `authentication.py`

Handles the SSO authentication flow:
- `attempt_login()`: Performs the complete CAS SSO login flow
- `perform_logout()`: Ends the session
- `format_*_response()`: Formats MCP TextContent responses

### `course_management.py`

Course-related operations:
- `get_courses()`: Retrieves enrolled courses from portfolio page
- `format_courses_response()`: Formats course list for MCP

### `html_parsing.py`

BeautifulSoup utilities for extracting data from HTML:
- `extract_sso_link()`: Finds SSO login button on eClass login page
- `extract_cas_form_data()`: Extracts CAS form parameters (execution token, action URL)
- `extract_courses()`: Parses course list from portfolio page
- `verify_login_success()`: Checks if login succeeded

## Session Management

The `SessionState` class wraps a `requests.Session` to:
- Persist cookies (especially `PHPSESSID`) across requests
- Track login status and username
- Cache course list
- Validate session by accessing protected resources

```python
class SessionState:
    session: requests.Session  # Cookie persistence
    logged_in: bool            # Login state flag
    username: str | None       # Current user
    courses: List[Dict]        # Cached course list
```

## Authentication Flow

The SSO login follows UoA's CAS protocol:

1. **Visit eClass login page** (`/main/login_form.php`)
2. **Find SSO link** - Parse HTML for "Είσοδος με λογαριασμό ΕΚΠΑ" link
3. **Follow to CAS** - Redirects to `sso.uoa.gr/login`
4. **Extract form data** - Get `execution` token and form `action` from CAS page
5. **Submit credentials** - POST username, password, execution, `_eventId=submit`
6. **Follow redirect** - CAS redirects back to eClass with ticket
7. **Verify login** - Access portfolio page to confirm authentication

## Configuration

Environment variables (loaded from `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `ECLASS_URL` | `https://eclass.uoa.gr` | Base URL |
| `ECLASS_SSO_DOMAIN` | `sso.uoa.gr` | SSO server domain |
| `ECLASS_SSO_PROTOCOL` | `https` | SSO protocol (http for local testing) |
| `ECLASS_USERNAME` | - | Login username |
| `ECLASS_PASSWORD` | - | Login password |

## Standalone Client

The `eclass_client.py` provides the same functionality without MCP:

```python
from eclass_mcp_server import authentication, html_parsing

class EClassClient:
    # Reuses authentication.attempt_login() and html_parsing.* functions
```

This demonstrates that the core logic is decoupled from MCP and can be used independently.
