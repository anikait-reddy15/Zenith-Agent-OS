import asyncio
from contextlib import AsyncExitStack
from typing import Any, Dict, List
import shutil

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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

import sys
import shutil

async def test_run():
    """Test function to check if connection to the MCP server is being established or not"""
    # 1. Use shutil.which to find the exact absolute path of npx
    npx_path = shutil.which("npx")
    
    # 2. Safety check: If it can't find it, stop and warn the user
    if not npx_path:
        print("ERROR: Could not find 'npx' on your system.")
        print("Please ensure Node.js is installed and you have restarted your terminal.")
        return

    print(f"Found npx at: {npx_path}")

    # 3. Use the absolute path in the MCP Client
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
    import asyncio
    asyncio.run(test_run())