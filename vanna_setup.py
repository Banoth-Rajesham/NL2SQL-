import os
import sqlite3
import asyncio
import logging
from dotenv import load_dotenv

# ---------- LOAD ENV ----------
load_dotenv()

# ---------- VANNA IMPORTS ----------
from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import User
from vanna.core.user.request_context import RequestContext
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.openai import OpenAILlmService

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VANNA_SETUP")

# ---------- USER ----------
class SimpleUserResolver:
    async def resolve_user(self, _):
        return User(id="user_001", username="admin")

# ---------- LLM ----------
# Using a very stable Groq model for high availability
GROQ_MODEL = "llama-3.1-8b-instant" 

llm = OpenAILlmService(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    model=GROQ_MODEL
)

# ---------- DATABASE ----------
db = SqliteRunner("clinic.db")

# ---------- SQL SAFETY OVERRIDE ----------
# We use our own safety in main.py, but db runner needs select-only for security
original_run_sql = db.run_sql

def select_only_run_sql(sql):
    if not sql: return "EMPTY_SQL"
    s = sql.upper().strip()
    if not s.startswith("SELECT"): return "ERROR: ONLY_SELECT_ALLOWED"
    return original_run_sql(sql)

db.run_sql = select_only_run_sql

# ---------- MEMORY ----------
memory = DemoAgentMemory()

# ---------- TOOLS ----------
tools = ToolRegistry()
tools.register_local_tool(RunSqlTool(db), access_groups=[])
tools.register_local_tool(VisualizeDataTool(), access_groups=[])
tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=[])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=[])

# ---------- AGENT ----------
agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    agent_memory=memory,
    user_resolver=SimpleUserResolver()
)

# ---------- DATA MODEL ----------
def get_detailed_schema():
    """Extract schema with table names and columns for the LLM context"""
    try:
        conn = sqlite3.connect("clinic.db")
        cur = conn.cursor()
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        schema_info = []
        for (table_name,) in tables:
            if table_name.startswith('sqlite_'): continue
            cols = cur.execute(f"PRAGMA table_info({table_name})").fetchall()
            col_list = [f"{c[1]} ({c[2]})" for c in cols]
            schema_info.append(f"Table '{table_name}' columns: " + ", ".join(col_list))
        conn.close()
        return "\n".join(schema_info)
    except Exception as e:
        return f"Error loading schema: {e}"

# Pre-load schema text
SCHEMA_HELP = get_detailed_schema()

def get_schema_for_llm():
    return SCHEMA_HELP

def make_request_context(metadata: dict = None) -> RequestContext:
    return RequestContext(metadata=metadata or {})

# ---------- EXTRACT CONTENT FROM STREAM ----------
def extract_text_from_component(component) -> str:
    """Robust extractor that checks multiple fields in Vanna UiComponent objects"""
    if not component: return ""
    text_buffer = []
    
    # Check simple_component
    sc = getattr(component, 'simple_component', None)
    if sc:
        if hasattr(sc, 'text'): text_buffer.append(str(sc.text))
    
    # Check rich_component (can be StatusBar, StatusCard, RichText, etc.)
    rc = getattr(component, 'rich_component', None)
    if rc:
        for attr in ['content', 'text', 'description', 'message', 'title']:
            val = getattr(rc, attr, None)
            if val: text_buffer.append(str(val))
    
    # If standard fields are empty, try string representation as a last resort
    # But only if it's not a generic object string
    if not text_buffer:
        res = str(component)
        if "UiComponent" not in res and "<" not in res:
            text_buffer.append(res)
            
    return " ".join(text_buffer)

# ---------- TEST SCRIPT ----------
async def test_agent():
    print("Testing Groq Agent Connectivity...")
    ctx = make_request_context({"env": "test"})
    q = "How many patients exist?"
    print(f"Question: {q}")
    
    try:
        async for r in agent.send_message(ctx, q):
            text = extract_text_from_component(r)
            if text: print(f"  [Chunk]: {text}")
        print("Test Complete.")
    except Exception as e:
        print(f"Fatal Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent())