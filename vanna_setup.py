import os
import sqlite3
import asyncio
from dotenv import load_dotenv

# ---------- LOAD ENV ----------
load_dotenv()

# ---------- VANNA IMPORTS ----------
from vanna import Agent
from vanna.core.registry import ToolRegistry
from vanna.core.user import User
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.openai import OpenAILlmService

# ---------- USER ----------
class SimpleUserResolver:
    async def resolve_user(self, _):
        return User(id="user", username="user")

# ---------- LLM ----------
llm = OpenAILlmService(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    model="llama-3.3-70b-versatile"
)

# ---------- DATABASE ----------
db = SqliteRunner("clinic.db")

# ---------- SIMPLE SQL SAFETY ----------
original_run_sql = db.run_sql

def safe_run_sql(sql):
    sql_upper = sql.upper()

    # allow only SELECT
    if not sql_upper.strip().startswith("SELECT"):
        return "Only SELECT allowed"

    # block dangerous words
    bad_words = ["INSERT","UPDATE","DELETE","DROP","ALTER","EXEC","XP_","SP_","GRANT","REVOKE","SHUTDOWN","SQLITE_MASTER"]
    if any(w in sql_upper for w in bad_words):
        return "Dangerous SQL blocked"

    try:
        return original_run_sql(sql)
    except Exception as e:
        return str(e)

# replace default
db.run_sql = safe_run_sql

# ---------- MEMORY ----------
memory = DemoAgentMemory()

# ---------- TOOLS ----------
tools = ToolRegistry()

tools.register_local_tool(RunSqlTool(db), access_groups=[])
tools.register_local_tool(VisualizeDataTool(), access_groups=[])

# memory tools
tools.register_local_tool(SaveQuestionToolArgsTool(memory), access_groups=[])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(memory), access_groups=[])

# ---------- AGENT ----------
agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    agent_memory=memory,
    user_resolver=SimpleUserResolver()
)

# ---------- LOAD SCHEMA (SIMPLE) ----------
def load_schema():
    conn = sqlite3.connect("clinic.db")
    cur = conn.cursor()

    tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

    text = ""
    for t in tables:
        name = t[0]
        cols = cur.execute(f"PRAGMA table_info({name})").fetchall()

        text += f"{name}: "
        text += ", ".join([c[1] for c in cols])
        text += "\n"

    conn.close()

    try:
        memory.add({"role": "system", "content": text})
    except:
        pass

# load schema
load_schema()

# ---------- TEST ----------
async def test():
    class Req:
        metadata = {}

    res = agent.send_message("How many patients are there?", request_context=Req())

    async for r in res:
        print(r)

if __name__ == "__main__":
    asyncio.run(test())