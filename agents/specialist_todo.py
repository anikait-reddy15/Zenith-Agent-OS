import os
import sqlite3
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

# 2. Database Initialization
PROJECT_DIR = os.path.abspath("C:/Projects/Zenith-Agent-OS")
DB_PATH = os.path.join(PROJECT_DIR, "tasks.db")

def init_db():
    """Creates the SQLite database and tasks table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

# Run initialization immediately when this file is imported
init_db()

# 3. Define the Tools
class AddTaskArgs(BaseModel):
    description: str = Field(description="The description of the task to add.")

@tool
def add_task(description: str) -> str:
    """Adds a new task to the user's to-do list."""
    print(f"[Tool Execution] Adding task: {description}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (description) VALUES (?)", (description,))
        conn.commit()
        task_id = cursor.lastrowid
        conn.close()
        return f"Successfully added task #{task_id}: '{description}'"
    except Exception as e:
        return f"Database Error: {str(e)}"

class ListTasksArgs(BaseModel):
    status: str = Field(
        description="Filter by status: 'pending', 'completed', or 'all'. Default is 'pending'.", 
        default="pending"
    )

@tool
def list_tasks(status: str = "pending") -> str:
    """Lists tasks from the database based on their status."""
    print(f"[Tool Execution] Listing {status} tasks...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        if status.lower() == 'all':
            cursor.execute("SELECT id, description, status FROM tasks")
        else:
            cursor.execute("SELECT id, description, status FROM tasks WHERE status = ?", (status.lower(),))
        tasks = cursor.fetchall()
        conn.close()
        
        if not tasks:
            return f"No {status} tasks found."
        
        result = f"--- {status.upper()} TASKS ---\n"
        for t in tasks:
            result += f"[{t[0]}] {t[1]} ({t[2]})\n"
        return result
    except Exception as e:
        return f"Database Error: {str(e)}"

class CompleteTaskArgs(BaseModel):
    task_id: int = Field(description="The numeric ID of the task to mark as completed.")

@tool
def complete_task(task_id: int) -> str:
    """Marks a specific task as completed using its ID."""
    print(f"[Tool Execution] Completing task #{task_id}")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
        changes = conn.total_changes
        conn.commit()
        conn.close()
        
        if changes == 0:
            return f"Task #{task_id} not found."
        return f"Successfully marked task #{task_id} as completed."
    except Exception as e:
        return f"Database Error: {str(e)}"

# 4. Compile the Agent
todo_tools = [add_task, list_tasks, complete_task]
todo_agent = create_react_agent(llm, todo_tools)