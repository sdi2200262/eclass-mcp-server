# How the eClass MCP Server Works

<p align="center">
    <strong>Technical deep-dive into the eClass MCP Server implementation</strong>
</p>

This document explains the core architecture and implementation details of the eClass MCP Server. It covers how the server initializes, manages state, handles requests, and processes tools.

## Architecture Overview

The eClass MCP Server follows a modular architecture that separates concerns and improves maintainability:

```
server.py             # Core MCP server setup, tool registration, and request handling
├── authentication.py # Authentication with eClass and SSO system
├── course_management.py # Course-related functionality
└── html_parsing.py   # HTML parsing utilities
```

This separation allows each component to focus on a specific responsibility:
- `server.py` - Handles MCP protocol communication and tool dispatch
- `authentication.py` - Manages login, logout, and session verification
- `course_management.py` - Retrieves and formats course information
- `html_parsing.py` - Extracts data from eClass HTML responses

## Server Initialization

The server initialization happens in two phases:

### Phase 1: Configuration and Registration

```python
# Initialize the MCP server
server = Server("eclass-mcp")

# Register handlers with decorators
@server.list_tools()
async def handle_list_tools():
    # List of available tools...

@server.call_tool()
async def handle_call_tool(name, arguments):
    # Tool dispatch logic...
```

This phase defines what the server can do by registering handlers for various MCP protocol operations.

### Phase 2: Full Initialization and Running

```python
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="eclass-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(...),
            ),
        )
```

This phase sets up the transport (stdio), provides complete initialization options, and actually starts the server.

## Session State Management

One of the core challenges in implementing an MCP server is maintaining state between calls, as the MCP protocol itself is stateless. The eClass MCP Server solves this with a `SessionState` class:

```python
# Global session state - maintains authentication state between calls
class SessionState:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize session and state
        self.session = requests.Session()
        self.logged_in = False
        
        # Set base URL and other properties...
        
    def is_session_valid(self) -> bool:
        """Check if the current session is still valid without full re-auth."""
        # Session validation logic...
        
    def reset(self):
        """Reset the session state."""
        # Reset session state...

# Initialize global session state
session_state = SessionState()
```

This approach allows the server to:
1. Maintain an authenticated session with eClass
2. Track login state across multiple tool calls
3. Validate session before operations
4. Reset cleanly when needed

## Request Handling Flow

When a client makes a request to the server, it follows this flow:

1. **Request Reception**: The MCP SDK receives the request via stdin/stdout
2. **Request Parsing**: The SDK parses the JSON-RPC message
3. **Handler Dispatch**: The request is routed to the appropriate handler:
   - `ListToolsRequest` → `handle_list_tools()`
   - `CallToolRequest` → `handle_call_tool()`
4. **Tool Dispatch**: For tool calls, the handler routes to the specific tool implementation
5. **Response Formatting**: Results are formatted as MCP-compatible responses
6. **Response Transmission**: The SDK sends the response back to the client

## Tool Registration and Implementation

Tools are registered using the `@server.list_tools()` decorator, which defines the available tools and their interfaces:

```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available eClass tools."""
    return [
        types.Tool(
            name="login",
            description="Log in to eClass...",
            inputSchema={...}
        ),
        # Additional tools...
    ]
```

When a tool is called, the `handle_call_tool()` function routes to the appropriate handler:

```python
@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle eClass tool execution requests."""
    if name == "login":
        return await handle_login({})
    elif name == "get_courses":
        return await handle_get_courses()
    # Additional tool handlers...
```

Each tool handler follows a similar pattern:
1. Check preconditions (e.g., authentication status)
2. Execute the tool's core functionality
3. Format the response using the appropriate MCP types
4. Return a standardized response

## Response Formatting

All tool responses are formatted using the MCP SDK's types, primarily `TextContent`:

```python
def format_login_response(success: bool, message: Optional[str], username: Optional[str] = None) -> types.TextContent:
    """Format login response for MCP."""
    if success:
        return types.TextContent(
            type="text",
            text=f"Login successful! You are now logged in as {username}.",
        )
    else:
        return types.TextContent(
            type="text",
            text=f"Error: {message}",
        )
```

This consistent formatting ensures that all responses conform to the MCP protocol and can be properly interpreted by the client.

## Modular Component Integration

The server integrates its modular components by:

1. **Importing components**: 
   ```python
   from . import authentication
   from . import course_management
   from . import html_parsing
   ```

2. **Delegation to specialized functions**:
   ```python
   # In handle_login:
   success, message = authentication.attempt_login(session_state, username, password)
   return [authentication.format_login_response(success, message, username if success else None)]
   ```

3. **Sharing state** via the `session_state` object that is passed to component functions

This modular approach allows each component to focus on its specific domain while integrating seamlessly with the MCP server framework.

## Error Handling

The server implements robust error handling to ensure that:

1. Authentication failures are properly communicated to clients
2. Network errors don't crash the server
3. Session state is validated before operations
4. All errors are formatted as proper MCP error responses

For example:

```python
# In handle_login:
if not username or not password:
    return [
        types.TextContent(
            type="text",
            text="Error: Username and password must be provided in the .env file.",
        )
    ]
```

The MCP SDK also provides additional error handling for the protocol communication layer.

## Next Steps

For more detailed information about how the server integrates with the MCP Python SDK, see the [MCP SDK Integration](./mcp-sdk-integration.md) document. 