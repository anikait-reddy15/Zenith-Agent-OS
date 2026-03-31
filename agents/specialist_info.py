import os
import sys
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# 1. Setup the Brain
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing! Please check your .env file.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0,
    api_key=api_key
)

# 2. Native Python Filesystem Tools
PROJECT_DIR = os.path.abspath("C:/Projects/Zenith-Agent-OS")

class ReadFileArgs(BaseModel):
    path: str = Field(description="The absolute path of the file to read.")

@tool
def read_local_file(path: str) -> str:
    """Use this tool to read the contents of a file on the local filesystem."""
    safe_path = os.path.abspath(path)
    print(f"[Tool Execution] Reading file: {safe_path}")
    
    # Security check: Prevent the AI from reading files outside the project
    if not safe_path.startswith(PROJECT_DIR):
        return "Security Error: Cannot access files outside the project directory."
        
    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"System Error: {str(e)}"

class ListDirArgs(BaseModel):
    path: str = Field(description="The absolute path of the directory to list.")

@tool
def list_local_directory(path: str) -> str:
    """Use this tool to list the files and folders inside a directory."""
    safe_path = os.path.abspath(path)
    print(f"[Tool Execution] Listing directory: {safe_path}")
    
    # Security check: Prevent the AI from exploring outside the project
    if not safe_path.startswith(PROJECT_DIR):
        return "Security Error: Cannot access directories outside the project."
        
    try:
        items = os.listdir(safe_path)
        return f"Contents of {safe_path}:\n" + "\n".join(items)
    except Exception as e:
        return f"System Error: {str(e)}"

# 3. Compile the Agent
fs_tools = [read_local_file, list_local_directory]
fs_agent = create_react_agent(llm, fs_tools)