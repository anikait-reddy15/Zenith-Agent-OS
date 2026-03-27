import asyncio
import os
import sys
import shutil
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.mcp_client import AgentMCPClient

# Load API Keys from .env
load_dotenv()

# Tell Python to look for 'GEMINI_API_KEY' instead of 'GOOGLE_API_KEY'
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing! Please check your .env file.")

# 1. Setup the Brain (Gemini) and the Hands (MCP)
# Using Gemini 2.5 Flash: It is incredibly fast and cheap, perfect for Scale-to-Zero API agents.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, api_key=api_key)

# Initialize our MCP Client globally so tools can use it
npx_path = shutil.which("npx")
mcp_client = AgentMCPClient(command=npx_path, args=["-y", "@modelcontextprotocol/server-memory"])


# 2. Create the LangChain/MCP Bridge Tool
# We define the exact data structure the MCP memory server expects.
# This guides Gemini so it doesn't hallucinate the wrong JSON formats.
class Entity(BaseModel):
    name: str = Field(description="The name of the entity.")
    entityType: str = Field(description="The type of the entity (e.g., Person, Event, Project, Concept).")
    observations: list[str] = Field(description="A list of facts or observations about this entity.")

@tool
async def save_to_memory(entities: list[Entity]) -> str:
    """Use this tool to save important information, facts, or context into the persistent memory graph."""
    
    # Convert Gemini's Pydantic objects into standard dictionaries for the MCP client
    entities_dict = [{"name": e.name, "entityType": e.entityType, "observations": e.observations} for e in entities]
    
    print(f"\n[Tool Execution] Saving {len(entities)} entities to MCP Memory Server...")
    
    # Execute the actual MCP tool we tested earlier
    result = await mcp_client.execute_tool(
        tool_name="create_entities",
        arguments={"entities": entities_dict}
    )
    return str(result)

# 3. Compile the Agent
# create_react_agent automatically builds the graph that loops between the LLM and the tools
agent_tools = [save_to_memory]
memory_agent = create_react_agent(llm, agent_tools)

# 4. Test the Agent
async def test_agent():
    # Update this check to match your new environment variable
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not found in .env file.")
        return

    print("Starting MCP Server...")
    await mcp_client.connect()

    try:
        # Give the agent a plain-English command that requires memory storage
        user_prompt = "I am building an AI agent project named GUIDE. It interacts with desktop operating systems like Windows and Linux. Please save this."
        
        print(f"\nUser: {user_prompt}")
        print("Agent is thinking...\n")
        
        # The agent state requires a list of messages
        state = {"messages": [("user", user_prompt)]}
        
        # Stream the agent's thought process step-by-step
        async for chunk in memory_agent.astream(state):
            for node_name, output in chunk.items():
                print(f"--- [Node: {node_name.upper()}] ---")
                # Print the content generated at this step
                if "messages" in output:
                    message = output["messages"][-1]
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        print(f"Agent decided to use tool: {message.tool_calls[0]['name']}")
                    elif message.content:
                        print(f"Output: {message.content}")

    finally:
        await mcp_client.close()

if __name__ == "__main__":
    asyncio.run(test_agent())