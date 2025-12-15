# Wire Protocol Reference

This document defines the wire protocol compliance standards for the eClass MCP Server. It details the exact JSON-RPC 2.0 messages used by this server implementation.

## 1. Handshake (`initialize`)

The server initializes with specific metadata and capabilities.

**Response Structure:**

```json
{
  "protocolVersion": "2025-03-26", 
  "capabilities": {
    "tools": {
      "listChanged": false
    },
    "prompts": {},
    "resources": {}
  },
  "serverInfo": {
    "name": "eclass-mcp",
    "version": "0.1.0"
  }
}
```

## 2. Tool Listing (`tools/list`)

The server exposes the following tools. Note that all tools currently require a dummy `random_string` parameter to satisfy MCP schema requirements for tools without arguments.

**Response Structure:**

```json
{
  "tools": [
    {
      "name": "login",
      "description": "Log in to eClass using username/password from your .env file through UoA's SSO. Configure ECLASS_USERNAME and ECLASS_PASSWORD in your .env file.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "random_string": {
            "type": "string",
            "description": "Dummy parameter for no-parameter tools"
          }
        },
        "required": ["random_string"]
      }
    },
    {
      "name": "get_courses",
      "description": "Get list of enrolled courses from eClass",
      "inputSchema": {
        "type": "object",
        "properties": {
          "random_string": {
            "type": "string",
            "description": "Dummy parameter for no-parameter tools"
          }
        },
        "required": ["random_string"]
      }
    },
    {
      "name": "logout",
      "description": "Log out from eClass",
      "inputSchema": {
        "type": "object",
        "properties": {
          "random_string": {
            "type": "string",
            "description": "Dummy parameter for no-parameter tools"
          }
        },
        "required": ["random_string"]
      }
    },
    {
      "name": "authstatus",
      "description": "Check authentication status with eClass",
      "inputSchema": {
        "type": "object",
        "properties": {
          "random_string": {
            "type": "string",
            "description": "Dummy parameter for no-parameter tools"
          }
        },
        "required": ["random_string"]
      }
    }
  ]
}
```

## 3. Tool Execution (`tools/call`)

The server exclusively uses `TextContent` for responses. It does not use `ImageContent` or `EmbeddedResource`.

### Success Response

```json
{
  "content": [
    {
      "type": "text",
      "text": "Login successful! You are now logged in as [username]."
    }
  ],
  "isError": false
}
```

### Error Response

Application-level errors (e.g., "Invalid credentials") are returned as successful tool executions with an error message in the text content.

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: [Error Message]"
    }
  ],
  "isError": false 
}
```
