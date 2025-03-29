# MCP SDK Integration

<p align="center">
    <strong>How the eClass MCP Server integrates with the Model Context Protocol Python SDK</strong>
</p>

This document details how the eClass MCP Server uses the [Model Context Protocol (MCP) Python SDK](https://github.com/modelcontextprotocol/python-sdk) to communicate with AI clients. It explains which components are used, how they work, and how the server handles the protocol.

## SDK Overview

The Model Context Protocol provides a standardized way for tools, data sources, and AI models to communicate. The eClass MCP Server uses the low-level server API from the Python SDK to handle protocol messages, register tools, and format responses. 

## SDK Components Used

The server imports the following components from the MCP SDK:

```python
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
```

Each import has a specific purpose:

1. `InitializationOptions` - Used to configure the server when it starts
2. `mcp.types` - Provides data structures for tools, responses, and requests
3. `NotificationOptions` - Configures notification capabilities
4. `Server` - The core class that handles the MCP protocol
5. `mcp.server.stdio` - Handles stdin/stdout communication

## Server Initialization with SDK

The server is initialized using the `Server` class:

```python
# Initialize the MCP server
server = Server("eclass-mcp")
```

This creates a server instance with the name "eclass-mcp". The server is later run with full initialization options:

```python
await server.run(
    read_stream,
    write_stream,
    InitializationOptions(
        server_name="eclass-mcp",
        server_version="0.1.0",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(),
            experimental_capabilities={},
        ),
    ),
)
```

The `InitializationOptions` includes:
- Server name and version
- Capabilities derived from registered handlers
- Notification options (not actively used in this implementation)

## Handler Registration Through Decorators

The SDK provides decorator functions that register handlers for various MCP protocol operations. The server uses two key decorators:

### @server.list_tools()

This decorator registers a function to handle tool listing requests:

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
        # More tools...
    ]
```

Under the hood, this decorator:
1. Creates an internal handler function
2. Registers it to respond to `ListToolsRequest` messages
3. Stores the handler in the server's `request_handlers` dictionary

### @server.call_tool()

This decorator registers a function to handle tool execution requests:

```python
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any] | None
) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle eClass tool execution requests."""
    if name == "login":
        return await handle_login({})
    # More tool handling...
```

The decorator creates an internal handler that:
1. Extracts the tool name and arguments from the request
2. Calls the registered function with those parameters
3. Formats the result as a proper MCP response
4. Handles exceptions by converting them to error responses

## MCP Data Types Usage

The server uses several data types from the `mcp.types` module:

### types.Tool

Used to define tools exposed by the server:

```python
types.Tool(
    name="login",
    description="Log in to eClass...",
    inputSchema={
        "type": "object",
        "properties": {...},
        "required": [...],
    },
)
```

The `inputSchema` is a JSON Schema that defines what parameters the tool accepts.

### types.TextContent

In the `authentication.py`,`course_management.py` modules we include `format_tool_response()` functions. These functions make use of the types.TextContent class to format text responses:

```python
types.TextContent(
    type="text",
    text="Login successful! You are now logged in as username.",
)
```

This ensures responses conform to the MCP protocol format.

### Other Available Types

The SDK also supports other response types that aren't currently used by the server:
- `types.ImageContent` - For returning images
- `types.EmbeddedResource` - For returning embedded resources

## Protocol Communication

The MCP protocol is based on JSON-RPC 2.0, and the SDK handles all the details:

### Communication Setup

```python
async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
    await server.run(
        read_stream,
        write_stream,
        InitializationOptions(...),
    )
```

This sets up:
1. A read stream for incoming messages
2. A write stream for outgoing messages
3. Communication using stdin/stdout

### Message Flow

1. **Client to Server**: 
   - Client sends a JSON-RPC request message
   - SDK parses the message into a structured request object
   - SDK routes the request to the appropriate handler

2. **Server to Client**: 
   - Handler returns a structured response
   - SDK converts the response to a JSON-RPC message
   - SDK sends the message to the client

## Error Handling Through SDK

The SDK provides several layers of error handling:

### Handler-Level Errors

The `@server.call_tool()` decorator wraps the handler function in a try-except block:

```python
try:
    results = await func(req.params.name, (req.params.arguments or {}))
    return types.ServerResult(
        types.CallToolResult(content=list(results), isError=False)
    )
except Exception as e:
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=str(e))],
            isError=True,
        )
    )
```

This ensures that exceptions in tool execution are converted to proper error responses, avoiding potential server crashes.

### Protocol-Level Errors

The SDK also handles protocol-level errors, such as:
- Malformed requests
- Unknown method calls
- Invalid parameters

These are converted to appropriate JSON-RPC error responses.

## Low-Level vs. High-Level APIs

The MCP SDK provides two APIs:

1. **Low-Level API** (used by this server):
   - More control over protocol handling
   - Explicit handler registration
   - Direct access to request and response objects

2. **High-Level API** (`FastMCP`):
   - More ergonomic interface
   - Simplified handler registration
   - Automatic type conversion

The eClass MCP Server uses the low-level API for maximum control over request handling and response formatting.

## Next Steps

For detailed information about the specific tools implemented by the server, see the [Tools Reference](./tools-reference.md) document. 