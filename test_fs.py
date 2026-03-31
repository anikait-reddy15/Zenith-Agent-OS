import asyncio
import os
import shutil
import sys
from tools.mcp_client import AgentMCPClient

async def main():
    npx_path = shutil.which("npx")
    project_dir = "C:/Projects/Zenith-Agent-OS"
    
    print("Starting Filesystem MCP Server...")
    client = AgentMCPClient(command=npx_path, args=["-y", "@modelcontextprotocol/server-filesystem", project_dir])
    await client.connect()
    
    test_path = "C:/Projects/Zenith-Agent-OS/agents"
    print(f"\nSending command to list: {test_path}")
    
    try:
        # Ask Node.js to read the directory
        result = await asyncio.wait_for(
            client.execute_tool("list_directory", {"path": test_path}),
            timeout=5.0
        )
        print("\nSUCCESS! The server replied:")
        print(result)
    except Exception as e:
        print(f"\nERROR: {e}")
        
    await client.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())