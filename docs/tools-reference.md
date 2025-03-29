# Tools Reference

<p align="center">
    <strong>Comprehensive reference for all tools provided by the eClass MCP Server</strong>
</p>

<p align="center">
    <img src="../assets/guy-not-to-worry-about.png" alt="Meme">
</p>

This document provides detailed information about each tool exposed by the eClass MCP Server, including their purpose, parameters, response formats, and example usage.

## Tool Overview

The eClass MCP Server provides the following tools:

| Tool Name    | Description                                       | Authentication Required |
|--------------|---------------------------------------------------|-------------------------|
| login        | Authenticate with eClass through UoA's SSO system | No (obv)                |
| get_courses  | Retrieve a list of enrolled courses               | Yes                     |
| logout       | Log out from eClass                               | No (obv)                |
| authstatus   | Check current authentication status               | No                      |

## login

The login tool authenticates with the eClass platform using credentials stored in the `.env` file.

### Description

This tool initiates a multi-step authentication process:
1. Visit the eClass login page
2. Follow the SSO authentication link
3. Authenticate with UoA's CAS system
4. Verify successful authentication
5. Establish a session for subsequent requests

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

Note: The `random_string` parameter is a dummy parameter since the MCP protocol requires parameters. The actual username and password must be configured in the `.env` file. This ensures that no data leak of private information is possible when using the eClass MCP server.

### Response Format

Successful login:
```json
{
  "type": "text",
  "text": "Login successful! You are now logged in as username."
}
```

Failed login:
```json
{
  "type": "text",
  "text": "Error: [specific error message]"
}
```

Potential error messages:
- "Username and password must be provided in the .env file"
- "Could not find SSO login link on the login page"
- "Authentication error: Invalid credentials"
- "Network error during login process"

### Example Usage

```python
# Using the MCP client
login_result = await session.call_tool("login", {
    "random_string": "any_value"
})
print(login_result)
```

### Notes

- The tool automatically detects if you're already logged in and will return an appropriate message
- If the session has expired, it will automatically attempt to re-authenticate
- All authentication credentials must be stored in the `.env` file, not passed as parameters

## get_courses

The get_courses tool retrieves a list of courses the user is enrolled in from eClass.

### Description

This tool:
1. Verifies that the user is authenticated
2. Fetches the portfolio page from eClass
3. Extracts course information from the HTML
4. Returns a formatted list of courses

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

### Response Format

Successful course retrieval:
```json
{
  "type": "text",
  "text": "Found X courses:\n\n1. Course Name 1\n2. Course Name 2\n..."
}
```

Failed course retrieval:
```json
{
  "type": "text",
  "text": "Error: [specific error message]"
}
```

Potential error messages:
- "Not logged in. Please log in first using the login tool."
- "Session expired. Please log in again."
- "Network error retrieving courses"
- "No courses found. You may not be enrolled in any courses."

### Example Usage

```python
# Using the MCP client
courses_result = await session.call_tool("get_courses", {
    "random_string": "any_value"
})
print(courses_result)
```

### Notes

- This tool requires prior authentication using the login tool
- Course information includes only names, not detailed information
- The tool automatically handles session validation

## logout

The logout tool ends the current eClass session.

### Description

This tool:
1. Checks if there's an active session
2. Sends a logout request to eClass
3. Clears the session state

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

### Response Format

Successful logout:
```json
{
  "type": "text",
  "text": "Successfully logged out user username."
}
```

Not logged in:
```json
{
  "type": "text",
  "text": "Not logged in, nothing to do."
}
```

Failed logout:
```json
{
  "type": "text",
  "text": "Error during logout: [specific error message]"
}
```

### Example Usage

```python
# Using the MCP client
logout_result = await session.call_tool("logout", {
    "random_string": "any_value"
})
print(logout_result)
```

### Notes

- This tool can be called even if not logged in (it will respond appropriately)
- After logout, you'll need to use the login tool again to access authenticated resources

## authstatus

The authstatus tool checks the current authentication status with eClass.

### Description

This tool:
1. Checks if there's an active session
2. Verifies if the session is still valid
3. Reports the authentication status

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

### Response Format

Not logged in:
```json
{
  "type": "text",
  "text": "Status: Not logged in"
}
```

Logged in:
```json
{
  "type": "text",
  "text": "Status: Logged in as username\nCourses: X enrolled"
}
```

Session expired:
```json
{
  "type": "text",
  "text": "Status: Session expired. Please log in again."
}
```

### Example Usage

```python
# Using the MCP client
status_result = await session.call_tool("authstatus", {
    "random_string": "any_value"
})
print(status_result)
```

### Notes

- This tool is useful for checking if you need to log in before accessing authenticated resources
- It validates the current session without attempting to refresh it
- The response includes the number of courses if logged in

## Tool Error Handling

All tools follow consistent error handling patterns:

1. **Precondition Checking**: Tools verify necessary preconditions (e.g., authentication status)
2. **Specific Error Messages**: Each error scenario produces a descriptive error message
3. **Proper MCP Formatting**: All errors are formatted as proper MCP text responses
4. **Network Error Handling**: Network issues are caught and reported with descriptive messages

## Common Error Patterns

| Error Pattern                | Description                                      | Recommended Action                |
|------------------------------|--------------------------------------------------|-----------------------------------|
| Not logged in                | The requested operation requires authentication  | Call the login tool first         |
| Session expired              | The authentication session has expired           | Call the login tool to refresh    |
| Network error                | Connection to eClass failed                      | Check network and try again       |
| Missing credentials          | Username/password not found in .env file         | Configure the .env file properly  |
| Authentication error         | Invalid credentials or authentication failed     | Check credentials in .env file    |

## Back to Documentation Index

For details on how the server is implemented, see the [How It Works](./how-it-works.md) document. For information about MCP SDK integration, see the [MCP SDK Integration](./mcp-sdk-integration.md) document. For any other questions ask ChatGPT.