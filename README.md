# eClass MCP Server

<p aling="center">
    <strong>An MCP server for interacting with Open eClass platform instances, with specific support for UoA's SSO authentication system. </strong>
</p>


<p aling="center">
    <img src="assets/example.png" alt="Example Usecase">
</p>

<p aling="center">
    <strong>This server enables AI agents to authenticate with eClass, retrieve course information, and perform basic operations on the platform. </strong>
</p>


## Features

- **Authentication**: Log in to eClass through UoA's CAS SSO authentication system
- **Course Management**: Retrieve lists of enrolled courses
- **Session Management**: Maintain authenticated sessions between tool calls
- **Status Checking**: Verify authentication status

## Project Structure

This project follows a modular architecture for better maintainability:

```
eclass-mcp-server/
├── run_server.py               # Entry point script for running the server
├── pyproject.toml              # Project configuration and dependencies
├── .env                        # Environment variables (create from example.env)
├── src/
    └── eclass_mcp_server/      # Main package
        ├── __init__.py         # Package initialization
        ├── server.py           # Core server implementation and tool handlers
        ├── authentication.py   # Authentication functionality 
        ├── course_management.py # Course-related functionality
        ├── html_parsing.py     # HTML parsing utilities
        └── test/               # Test scripts for functionality verification
            ├── __init__.py
            ├── test_login.py
            ├── test_courses.py
            └── run_all_tests.py
```

## Installation

Install the server using UV (recommended):

```bash
# Clone the repository
git clone https://github.com/yourusername/eClass-MCP-server.git
cd eClass-MCP-server

# Install dependencies
uv sync --dev --all-extras
```

Alternatively, install with pip:

```bash
pip install -e .
```

## Configuration

Create a `.env` file in the root directory with the following configuration (or copy and rename the provided `example.env` file):

```
ECLASS_URL=https://eclass.uoa.gr
ECLASS_USERNAME=your_username
ECLASS_PASSWORD=your_password
```

All credentials must be provided in the .env file. The server does not accept credentials as parameters.

## Usage

### Terminal
Run the server using the entry point script:

```bash
python run_server.py
```

Or as a module:

```bash
python -m src.eclass_mcp_server.server
```

### Cursor
Go to Settings -> MCP. Click on `Add new MCP server`:

 - Select a unique but appropriate name so that the Agent knows what the server is for (e.g., "eClass Server")
 - Select the `command` option on "Type"
 - Add this in the command input: `python /path/to/eclass-mcp-server/run_server.py`

This command runs the `run_server.py` script that connects the MCP Client with the main server entry point in `server.py`.

<p aling="center">
    <img src="assets/cursor-server.png" alt="Cursor Server Card">
</p>

### Claude Desktop

To use with Claude Desktop:

1. Open Claude Desktop
2. Go to Settings > Server
3. Add a new server with the following details:
   - Name: eClass MCP
   - Command: Path to your run_server.py script
4. Click Add Server
5. Select the server from the dropdown when chatting with Claude

## Tools
The server provides the following tools for use with MCP clients:

### login

Log in to eClass using SSO authentication.

```json
{
  "random_string": "any_value"
}
```

### get_courses

Retrieve a list of enrolled courses (requires login first).

```json
{
  "random_string": "any_value"
}
```

### logout

Log out from eClass.

```json
{
  "random_string": "any_value"
}
```

### authstatus

Check the current authentication status.

```json
{
  "random_string": "any_value"
}
```

## Testing

The project includes test scripts to verify functionality:

```bash
# Run all tests
python -m src.eclass_mcp_server.test.run_all_tests

# Run specific tests
python -m src.eclass_mcp_server.test.test_login
python -m src.eclass_mcp_server.test.test_courses
```

## Example MCP Client Usage

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

async def run_agent():
    server_params = StdioServerParameters(
        command="python /path/to/eclass-mcp-server/run_server.py",
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # Login to eClass
            login_result = await session.call_tool("login", {
                "random_string": "dummy"
            })
            print(login_result)
            
            # Get courses
            courses_result = await session.call_tool("get_courses", {
                "random_string": "dummy"
            })
            print(courses_result)
            
            # Logout
            logout_result = await session.call_tool("logout", {
                "random_string": "dummy"
            })
            print(logout_result)

if __name__ == "__main__":
    asyncio.run(run_agent())
```

## Integration with AI Agents

This MCP server is designed to be used with AI agents that support the Model Context Protocol. This enables AI systems to interact with eClass directly, allowing for capabilities like:

- Retrieving course information
- Checking course announcements
- Accessing course materials
- Submitting assignments (future feature)

## Security Considerations

- The server handles sensitive authentication credentials
- Credentials are only used for authentication and are not stored persistently
- Session cookies are maintained in memory during the server's lifecycle
- The server validates session state before performing operations
- The `.env` file with credentials should never be committed to version control (it's included in .gitignore)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.