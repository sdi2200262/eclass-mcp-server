# eClass MCP Server Documentation

<strong>This documentation explains how the server works, how it integrates with the MCP SDK, and provides technical references</strong>

## Documentation Contents

This documentation provides detailed information about the eClass MCP Server implementation, architecture, and usage:

```
docs/
├── README.md                   # This documentation overview
├── architecture.md             # System architecture and design
└── reference/                  # Technical references
    ├── wire_protocol.md        # JSON-RPC protocol specification
    └── tools-reference.md      # Reference for available tools
```

## Documentation Sections

### [System Architecture](./architecture.md)

The `architecture.md` document provides a comprehensive explanation of the eClass MCP Server's architecture and implementation. It covers:

- Server initialization and configuration
- Session state management
- Authentication flow
- Modular architecture approach

### [Wire Protocol Reference](./reference/wire-protocol.md)

The `reference/wire-protocol.md` document defines the wire protocol compliance standards for the server. It details:

- Exact JSON-RPC 2.0 messages
- Handshake and initialization
- Tool listing and execution schemas

### [Tools Reference](./reference/tools-reference.md)

The `reference/tools-reference.md` document provides a technical reference for all tools exposed by the server:

- Complete list of available tools
- Input schema specifications
- Response format details
- Example usage with different clients

## Contributing to Documentation

Contributions to improve this documentation are welcome! Please consider:

- Following the established style and format
- Adding clear explanations with code examples where appropriate
- Updating documentation when functionality changes
- Creating diagrams or visual aids for complex concepts, if your change requires it

## Back to Main README

For installation instructions, configuration details, and usage examples, please refer to the [main README](../README.md) file. 