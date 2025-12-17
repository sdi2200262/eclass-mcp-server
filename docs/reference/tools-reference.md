# Tools Reference

Detailed documentation for all tools provided by the eClass MCP Server.

## Overview

| Tool | Description | Requires Auth |
|------|-------------|---------------|
| `login` | Authenticate via UoA SSO | No |
| `get_courses` | Retrieve enrolled courses | Yes |
| `logout` | End current session | No |
| `authstatus` | Check authentication status | No |

## login

Authenticates with eClass using credentials from the `.env` file.

### Authentication Flow

1. Visit eClass login page
2. Follow SSO authentication link
3. Authenticate with UoA's CAS system
4. Verify successful authentication
5. Establish session for subsequent requests

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "random_string": {
      "type": "string",
      "description": "Dummy parameter for no-parameter tools"
    }
  },
  "required": ["random_string"]
}
```

> **Note**: The `random_string` parameter is required by the MCP protocol. Actual credentials are read from `.env`.

### Responses

**Success:**
```json
{
  "type": "text",
  "text": "Login successful! You are now logged in as username."
}
```

**Already logged in:**
```json
{
  "type": "text",
  "text": "Already logged in as username"
}
```

**Error:**
```json
{
  "type": "text",
  "text": "Error: [specific error message]"
}
```

Possible errors:
- `"Username and password must be provided in the .env file"`
- `"Could not find SSO login link on the login page"`
- `"Authentication failed: Invalid credentials"`
- `"Network error during login process: [details]"`

---

## get_courses

Retrieves the list of enrolled courses from eClass.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "random_string": {
      "type": "string",
      "description": "Dummy parameter for no-parameter tools"
    }
  },
  "required": ["random_string"]
}
```

### Responses

**Success:**
```json
{
  "type": "text",
  "text": "Found X courses:\n\n1. Course Name\n   URL: https://eclass.uoa.gr/courses/ABC123/\n..."
}
```

**No courses:**
```json
{
  "type": "text",
  "text": "No courses found. You may not be enrolled in any courses."
}
```

**Error:**
```json
{
  "type": "text",
  "text": "Error: [specific error message]"
}
```

Possible errors:
- `"Not logged in. Please log in first using the login tool."`
- `"Session expired. Please log in again."`
- `"Network error retrieving courses: [details]"`

---

## logout

Ends the current eClass session.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "random_string": {
      "type": "string",
      "description": "Dummy parameter for no-parameter tools"
    }
  },
  "required": ["random_string"]
}
```

### Responses

**Success:**
```json
{
  "type": "text",
  "text": "Successfully logged out user username."
}
```

**Not logged in:**
```json
{
  "type": "text",
  "text": "Not logged in, nothing to do."
}
```

**Error:**
```json
{
  "type": "text",
  "text": "Error during logout: [specific error message]"
}
```

---

## authstatus

Checks the current authentication status.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "random_string": {
      "type": "string",
      "description": "Dummy parameter for no-parameter tools"
    }
  },
  "required": ["random_string"]
}
```

### Responses

**Logged in:**
```json
{
  "type": "text",
  "text": "Status: Logged in as username\nCourses: X enrolled"
}
```

**Not logged in:**
```json
{
  "type": "text",
  "text": "Status: Not logged in"
}
```

**Session expired:**
```json
{
  "type": "text",
  "text": "Status: Session expired. Please log in again."
}
```

---

## Common Error Patterns

| Error | Description | Resolution |
|-------|-------------|------------|
| Not logged in | Operation requires authentication | Call `login` first |
| Session expired | Session has timed out | Call `login` to refresh |
| Network error | Connection to eClass failed | Check network, retry |
| Missing credentials | `.env` file incomplete | Set `ECLASS_USERNAME` and `ECLASS_PASSWORD` |
| Authentication error | Invalid credentials | Verify credentials in `.env` |
