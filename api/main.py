import os
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.specialist_task import mcp_client
from agents.orchestrator import primary_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting FastAPI Server...")
    print("Connecting to Memory MCP Server...")
    await mcp_client.connect()
    
    yield
    
    print("Shutting down server...")
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
        # We must use HumanMessage for the Orchestrator StateGraph
        from langchain_core.messages import HumanMessage
        state = {"messages": [HumanMessage(content=request.prompt)]}
        
        # Call the Orchestrator
        final_state = await primary_agent.ainvoke(state)
        final_message = final_state["messages"][-1].content
        
        return ChatResponse(response=final_message)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # This tells Python to start the web server if you run the file directly
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=False)