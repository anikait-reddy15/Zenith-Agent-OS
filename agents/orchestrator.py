import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

# Import all our specialists
from agents.specialist_task import memory_agent
from agents.specialist_info import fs_agent
from agents.specialist_todo import todo_agent

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    api_key=api_key
)

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    next_node: str

class RouteDecision(BaseModel):
    step: str = Field(
        description="Choose 'todo_agent' to manage tasks or the database. Choose 'memory_agent' to save observations. Choose 'filesystem_agent' to read files. Choose 'general_chat' for normal questions."
    )

def supervisor_node(state: AgentState) -> AgentState:
    print("\n[Orchestrator] Analyzing user prompt...")
    router_llm = llm.with_structured_output(RouteDecision)
    system_prompt = SystemMessage(
        content="You are the Primary Orchestrator of Zenith Agent OS. Route the request to the correct specialist."
    )
    messages_to_analyze = [system_prompt] + state["messages"]
    decision = router_llm.invoke(messages_to_analyze)
    
    print(f"[Orchestrator] Routing task to: {decision.step}")
    return {"next_node": decision.step}

# --- Specialist Caller Nodes ---
async def call_memory_agent(state: AgentState) -> AgentState:
    print("[Specialist] Memory Agent activated.")
    response = await memory_agent.ainvoke({"messages": state["messages"]})
    return {"messages": [response["messages"][-1]]}

async def call_fs_agent(state: AgentState) -> AgentState:
    print("[Specialist] Filesystem Agent activated.")
    response = await fs_agent.ainvoke({"messages": state["messages"]})
    return {"messages": [response["messages"][-1]]}

async def call_todo_agent(state: AgentState) -> AgentState:
    print("[Specialist] To-Do Agent activated.")
    response = await todo_agent.ainvoke({"messages": state["messages"]})
    return {"messages": [response["messages"][-1]]}

def call_general_chat(state: AgentState) -> AgentState:
    print("[Specialist] General Chat activated.")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# --- Graph Building ---
builder = StateGraph(AgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("memory_agent", call_memory_agent)
builder.add_node("filesystem_agent", call_fs_agent)
builder.add_node("todo_agent", call_todo_agent)
builder.add_node("general_chat", call_general_chat)

def route_from_supervisor(state: AgentState) -> str:
    return state["next_node"]

builder.add_edge(START, "supervisor")
builder.add_conditional_edges(
    "supervisor",
    route_from_supervisor,
    {
        "memory_agent": "memory_agent",
        "filesystem_agent": "filesystem_agent",
        "todo_agent": "todo_agent",
        "general_chat": "general_chat"
    }
)

builder.add_edge("memory_agent", END)
builder.add_edge("filesystem_agent", END)
builder.add_edge("todo_agent", END)
builder.add_edge("general_chat", END)

primary_agent = builder.compile()