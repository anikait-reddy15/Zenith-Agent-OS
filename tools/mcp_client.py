import asyncio
from contextlib import AsyncExitStack
from typing import Any, Dict, List
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import mcp.types as types

class AgentMCPClient:
    def __init__(self, command: str, args: List[str]):
        """
        Initializes the client with the command to start the MCP server.
        Example: command="npx", args=["-y", "@modelcontextprotocol/server-memory"]
        """
        self.server_params = StdioServerParameters(
            command=command,
            args=args,
            env=None
        )
        self.session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()

    async def connect(self):
        """Establishes the stdio connection and initializes the MCP session."""
        print(f"Connecting to MCP Server: {self.server_params.command} {' '.join(self.server_params.args)}")
        
        # Open the standard input/output streams to the server
        stdio_transport = await self._exit_stack.enter_async_context(stdio_client(self.server_params))
        read_stream, write_stream = stdio_transport

        # Initialize the session protocol
        self.session = await self._exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        
        # The server requires a response to the 'roots/list' security check.
        # We access the private _request_handlers dictionary safely.
        for attr_name in dir(types):
            if "Root" in attr_name and "Request" in attr_name and "List" in attr_name:
                req_type = getattr(types, attr_name)
                
                async def handle_roots_list(*args, **kwargs):
                    # We explicitly grant the server access to your project folder
                    return types.ListRootsResult(roots=[
                        types.Root(uri="file:///C:/Projects/Zenith-Agent-OS", name="ProjectRoot")
                    ])
                    
                if hasattr(self.session, "_request_handlers"):
                    self.session._request_handlers[req_type] = handle_roots_list
                break

        await self.session.initialize()
        print("Connected and initialized successfully!")

    async def get_available_tools(self) -> List[Any]:
        """Fetches all tools provided by this specific MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")
        
        response = await self.session.list_tools()
        return response.tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Executes a tool on the server and returns the result."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect() first.")
        
        print(f"Executing tool: '{tool_name}' with args: {arguments}")
        result = await self.session.call_tool(tool_name, arguments)
        return result

    async def close(self):
        """Safely shuts down the connection."""
        await self._exit_stack.aclose()
        print("Connection closed.")

# Test Function
async def test_run():
    """Test function to check if connection to the MCP server is being established or not"""
    npx_path = shutil.which("npx")
    
    if not npx_path:
        print("ERROR: Could not find 'npx' on your system.")
        print("Please ensure Node.js is installed and you have restarted your terminal.")
        return

    print(f"Found npx at: {npx_path}")

    client = AgentMCPClient(command=npx_path, args=["-y", "@modelcontextprotocol/server-memory"])
    
    try:
        await client.connect()
        
        tools = await client.get_available_tools()
        print("\nAvailable Tools:")
        for tool in tools:
            print(f" - {tool.name}: {tool.description}")

        print("\nTesting Tool Execution:")
        result = await client.execute_tool(
            tool_name="create_entities",
            arguments={"entities": [{"name": "Hackathon", "entityType": "Event", "observations": ["Project is Scale-to-Zero"]}]}
        )
        print(f"Result: {result}")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_run())