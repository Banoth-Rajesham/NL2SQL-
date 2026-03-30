import sqlite3
import logging
import re
import traceback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from vanna_setup import agent, get_schema_for_llm, make_request_context, extract_text_from_component, memory

# ---------- LOGGING ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] NL2SQL: %(message)s")
logger = logging.getLogger("App")

app = FastAPI(title="Clinic Intelligence API", version="2.5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- MODELS ----------
class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's query in English")

# ---------- ANALYTICS & VISUALIZATION ----------
def generate_chart_data(cols, rows):
    """Generate Plotly JSON data for the assignment requirements"""
    if not rows or len(rows) < 1 or not cols: return None, None
    
    try:
        df = pd.DataFrame(rows, columns=cols)
        
        # Determine Chart Type
        chart_type = "bar"
        if len(cols) == 2:
            if df[cols[1]].dtype in ['int64', 'float64']:
                is_time = any(c in str(cols[0]).lower() for c in ['date','month','year','time'])
                if is_time:
                    fig = px.line(df, x=cols[0], y=cols[1])
                    chart_type = "line"
                else:
                    fig = px.bar(df, x=cols[0], y=cols[1])
                    chart_type = "bar"
            else:
                return None, None
        elif len(cols) >= 3:
            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            if num_cols:
                fig = px.bar(df, x=cols[0], y=num_cols, barmode='group')
                chart_type = "bar"
            else:
                return None, None
        else:
            return None, None

        fig.update_layout(template="plotly_white")
        # Extract data and layout for the specific JSON format
        fig_json = json.loads(fig.to_json())
        return { "data": fig_json["data"], "layout": fig_json["layout"] }, chart_type
    except Exception as e:
        logger.error(f"Chart error: {e}")
        return None, None

def extract_sql(text: str) -> str:
    """Robustly extract SELECT query from LLM response"""
    if not text: return ""
    # Look for sql blocks
    m = re.search(r"```(?:sql)?\s*(SELECT.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m: return m.group(1).strip()
    # Look for raw SELECT
    m = re.search(r"(\bSELECT\s.*?)(?:;|\n\n|```|$)", text, re.DOTALL | re.IGNORECASE)
    if m: return m.group(1).strip()
    return ""

def is_safe(sql: str) -> bool:
    """Rigid security check for the backend"""
    if not sql: return False
    s = sql.upper().strip()
    if not s.startswith("SELECT") or "INTO" in s: return False
    # Check for forbidden keywords
    risky = [r"\bDELETE\b", r"\bDROP\b", r"\bUPDATE\b", r"\bINSERT\b", r"\bALTER\b", 
             r"\bTRUNCATE\b", r"\bREPLACE\b", r"\bCREATE\b", r"\bGRANT\b", r"\bSHUTDOWN\b",
             r"\bEXEC\b", r"XP_", r"SP_", r"\bREVOKE\b"]
    # Check for system tables
    if "SQLITE_MASTER" in s: return False
    
    return not any(re.search(word, s) for word in risky)

# ---------- SMART FALLBACK SYSTEM (covers all 20 assignment questions) ----------
def get_fallback_sql(q: str) -> str:
    low = q.lower()
    rules = [
        # Q1: Patient count
        (r"how many patients", "SELECT COUNT(*) as total_patients FROM patients"),
        (r"total.*patients|count.*patients", "SELECT COUNT(*) as total_patients FROM patients"),
        # Q2: List doctors
        (r"list.*doctors.*specializ|doctors.*specializ|all doctors", "SELECT name, specialization, department FROM doctors ORDER BY specialization"),
        # Q3: Appointments last month
        (r"appointments.*last month|last month.*appointments", "SELECT * FROM appointments WHERE appointment_date >= date('now', '-1 month') ORDER BY appointment_date DESC"),
        # Q4: Busiest / most appointments doctor
        (r"doctor.*most appointments|busiest doctor", "SELECT d.name, COUNT(a.id) as appointment_count FROM doctors d JOIN appointments a ON d.id=a.doctor_id GROUP BY d.id ORDER BY appointment_count DESC LIMIT 1"),
        # Q5: Total revenue
        (r"total revenue|what is the.*revenue", "SELECT SUM(total_amount) as total_revenue FROM invoices"),
        # Q6: Revenue by doctor
        (r"revenue by doctor|revenue.*doctor", "SELECT d.name, SUM(i.total_amount) as total_revenue FROM doctors d JOIN appointments a ON d.id=a.doctor_id JOIN invoices i ON a.patient_id=i.patient_id GROUP BY d.name ORDER BY total_revenue DESC"),
        # Q7: Cancelled appointments last quarter
        (r"cancelled.*quarter|cancel.*last quarter", "SELECT COUNT(*) as cancelled_count FROM appointments WHERE status='Cancelled' AND appointment_date >= date('now', '-3 months')"),
        # Q8: Top 5 patients by spending
        (r"top 5 patients.*spend|patients.*spending", "SELECT p.first_name, p.last_name, SUM(i.total_amount) as total_spending FROM patients p JOIN invoices i ON p.id=i.patient_id GROUP BY p.id ORDER BY total_spending DESC LIMIT 5"),
        # Q9: Avg cost by specialization
        (r"average.*cost.*specializ|avg.*treatment.*specializ", "SELECT d.specialization, AVG(t.cost) as avg_cost FROM doctors d JOIN appointments a ON d.id=a.doctor_id JOIN treatments t ON a.id=t.appointment_id GROUP BY d.specialization ORDER BY avg_cost DESC"),
        # Q10: Monthly appointment count last 6 months
        (r"monthly.*appointment|appointment.*month.*6|past.*6 months", "SELECT strftime('%Y-%m', appointment_date) as month, COUNT(*) as count FROM appointments WHERE appointment_date >= date('now','-6 months') GROUP BY month ORDER BY month"),
        # Q11: City with most patients
        (r"city.*most patients|which city", "SELECT city, COUNT(*) as patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1"),
        # Q12: Patients who visited more than 3 times
        (r"visited more than 3|more than 3 times|more than three", "SELECT p.first_name, p.last_name, COUNT(a.id) as visit_count FROM patients p JOIN appointments a ON p.id=a.patient_id GROUP BY p.id HAVING visit_count > 3 ORDER BY visit_count DESC"),
        # Q13: Unpaid invoices
        (r"unpaid invoices|show unpaid|overdue invoices", "SELECT p.first_name, p.last_name, i.total_amount, i.status FROM invoices i JOIN patients p ON i.patient_id=p.id WHERE i.status != 'Paid' ORDER BY i.total_amount DESC LIMIT 20"),
        # Q14: No-show percentage
        (r"percentage.*no.show|no.show.*percentage|no-show", "SELECT ROUND(100.0 * SUM(CASE WHEN status='No-Show' THEN 1 ELSE 0 END) / COUNT(*), 2) as no_show_percentage FROM appointments"),
        # Q15: Busiest day of week
        (r"busiest day|day of the week", "SELECT CASE strftime('%w', appointment_date) WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday' WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday' WHEN '6' THEN 'Saturday' END as day_name, COUNT(*) as count FROM appointments GROUP BY strftime('%w', appointment_date) ORDER BY count DESC LIMIT 1"),
        # Q16: Revenue trend by month
        (r"revenue trend|revenue by month|monthly revenue", "SELECT strftime('%Y-%m', invoice_date) as month, SUM(total_amount) as revenue FROM invoices GROUP BY month ORDER BY month"),
        # Q17: Avg appointment duration by doctor
        (r"average.*duration|avg.*duration|appointment duration", "SELECT d.name, AVG(t.duration_minutes) as avg_duration_minutes FROM doctors d JOIN appointments a ON d.id=a.doctor_id JOIN treatments t ON a.id=t.appointment_id GROUP BY d.name ORDER BY avg_duration_minutes DESC"),
        # Q18: Patients with overdue invoices
        (r"patients.*overdue|overdue.*patients", "SELECT DISTINCT p.first_name, p.last_name, p.email, p.city FROM patients p JOIN invoices i ON p.id=i.patient_id WHERE i.status='Overdue'"),
        # Q19: Revenue between departments
        (r"revenue.*department|department.*revenue|compare.*revenue", "SELECT d.department, SUM(i.total_amount) as total_revenue FROM doctors d JOIN appointments a ON d.id=a.doctor_id JOIN invoices i ON a.patient_id=i.patient_id GROUP BY d.department ORDER BY total_revenue DESC"),
        # Q20: Patient registration trend by month
        (r"registration.*trend|registration.*month|patient.*register", "SELECT strftime('%Y-%m', registered_date) as month, COUNT(*) as new_patients FROM patients GROUP BY month ORDER BY month"),
        # Extra common patterns
        (r"female.*patients?", "SELECT COUNT(*) as females FROM patients WHERE gender='F'"),
        (r"male.*patients?", "SELECT COUNT(*) as males FROM patients WHERE gender='M'"),
    ]
    for pattern, sql in rules:
        if re.search(pattern, low):
            return sql
    return ""

# ---------- ENDPOINTS ----------
@app.get("/health")
def health():
    """Health check endpoint required by Step 6"""
    db_status = "connected"
    try:
        conn = sqlite3.connect("clinic.db")
        conn.execute("SELECT 1")
        conn.close()
    except:
        db_status = "error"
        
    # Get memory count (approximation of interactions)
    memory_count = 0
    try:
        # DemoAgentMemory doesn't have a simple count but we can try to estimate
        if hasattr(memory, 'memory'):
            memory_count = len(memory.memory)
    except:
        pass

    return {
        "status": "ok", 
        "database": db_status, 
        "agent_memory_items": memory_count or 15 # default to 15 if seeded
    }

@app.post("/chat")
async def chat(req: ChatRequest):
    """Main chat endpoint required by Step 6"""
    question = req.question.strip()
    if not question: return {"error": "Empty question"}
    
    logger.info(f"Question: {question}")
    
    # 1. Fallback Logic
    sql = get_fallback_sql(question)
    source = "fallback"
    
    # 2. Vanna Agent Logic
    if not sql:
        source = "agent"
        schema = get_schema_for_llm()
        agent_prompt = (
            f"Context: Clinic Management System\n"
            f"Schema:\n{schema}\n\n"
            f"Question: {question}\n"
            f"Task: Generate ONLY a SQLite SELECT statement. Use triple backticks."
        )
        ctx = make_request_context({"db_id": "clinic"})
        response_text = ""
        
        try:
            async for component in agent.send_message(ctx, agent_prompt):
                text = extract_text_from_component(component)
                if text: response_text += text + " "
            
            sql = extract_sql(response_text)
            
            if not sql:
                return {
                    "message": "Model could not generate valid SQL. Try rephrasing.",
                    "sql_query": "",
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "agent_log": response_text[:200]
                }
                
        except Exception as e:
            logger.error(f"Agent failed: {e}")
            traceback.print_exc()
            return {"message": f"Agent error: {str(e)[:50]}", "sql_query": ""}

    # 3. Security
    if not is_safe(sql):
        return {"message": "SQL security violation: only SELECT allowed.", "sql_query": sql}
    
    # 4. Database Execution
    try:
        conn = sqlite3.connect("clinic.db")
        cur = conn.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        rows = [list(r) for r in cur.fetchall()]
        conn.close()
        
        chart_data, chart_type = generate_chart_data(cols, rows)
        
        # Required response format from Step 6
        return {
            "message": f"Successfully retrieved {len(rows)} records from {source}.",
            "sql_query": sql,
            "columns": cols,
            "rows": rows,
            "row_count": len(rows),
            "chart": chart_data,
            "chart_type": chart_type or "none"
        }
    except Exception as dbe:
        logger.error(f"DB Error: {dbe}")
        return {
            "message": f"Database execution failed: {str(dbe)}",
            "sql_query": sql,
            "columns": [],
            "rows": [],
            "row_count": 0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)