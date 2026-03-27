import os
import sys
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Windows asyncio sub process
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Ensure Python can find our agents folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.specialist_task import memory_agent, mcp_client

# 1. Server Lifespan (Startup and Shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs when the server starts
    print("Starting FastAPI Server...")
    print("Connecting to MCP Server...")
    await mcp_client.connect()
    yield
    # This runs when the server shuts down
    print("Shutting down server and MCP connection...")
    await mcp_client.close()

# Initialize FastAPI
app = FastAPI(title="Zenith Agent OS", lifespan=lifespan)

# 2. API Data Models
class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

# 3. The API Endpoints
@app.get("/")
async def health_check():
    """A simple check to ensure the server is running."""
    return {"status": "online", "system": "Zenith Agent OS"}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Send a prompt to the LangGraph agent and get the final response."""
    try:
        # Prepare the state for LangGraph
        state = {"messages": [("user", request.prompt)]}
        
        # We use ainvoke instead of astream to just get the final result
        final_state = await memory_agent.ainvoke(state)
        
        # Extract the last message from the agent
        final_message = final_state["messages"][-1].content
        
        return ChatResponse(response=final_message)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # This tells Python to start the web server if you run the file directly
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=False)