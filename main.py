import os
import sqlite3
import logging
import hashlib
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px

from vanna_setup import agent

# ---------- LOGGING SETUP ----------
import sys
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors during startup
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress uvicorn verbose logs
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# ---------- SETUP ----------
load_dotenv()
app = FastAPI(title="NL2SQL API", version="1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- QUERY CACHING ----------
query_cache = {}
CACHE_TTL = 3600  # 1 hour in seconds

def get_cache_key(question):
    """Generate cache key from question"""
    return hashlib.md5(question.lower().strip().encode()).hexdigest()

def cache_get(question):
    """Get cached result if exists and not expired"""
    key = get_cache_key(question)
    if key in query_cache:
        result, timestamp = query_cache[key]
        if (datetime.now() - timestamp).total_seconds() < CACHE_TTL:
            logger.info(f"Cache HIT for question: {question[:50]}")
            return result
        else:
            del query_cache[key]
            logger.info(f"Cache EXPIRED for question: {question[:50]}")
    return None

def cache_set(question, result):
    """Store result in cache"""
    key = get_cache_key(question)
    query_cache[key] = (result, datetime.now())
    logger.info(f"Cached result for: {question[:50]}")

# ---------- RATE LIMITING ----------
client_requests = {}
RATE_LIMIT = 10  # 10 requests per minute
RATE_WINDOW = 60  # seconds

def check_rate_limit(client_id="default"):
    """Simple rate limiting per client"""
    now = datetime.now()
    
    if client_id not in client_requests:
        client_requests[client_id] = []
    
    # Remove old requests
    client_requests[client_id] = [
        req_time for req_time in client_requests[client_id]
        if (now - req_time).total_seconds() < RATE_WINDOW
    ]
    
    if len(client_requests[client_id]) >= RATE_LIMIT:
        logger.warning(f"Rate limit exceeded for client: {client_id}")
        return False
    
    client_requests[client_id].append(now)
    return True

# ---------- REQUEST ----------
class ChatRequest(BaseModel):
    question: str

    class Config:
        json_schema_extra = {
            "example": {"question": "How many patients are there?"}
        }

# ---------- INPUT VALIDATION ----------
def validate_input(question: str) -> tuple[bool, str]:
    """Validate user input"""
    # Check if empty
    if not question or len(question.strip()) == 0:
        logger.warning("Empty question received")
        return False, "Question cannot be empty"
    
    # Check length (min 3 chars, max 500 chars)
    if len(question.strip()) < 3:
        logger.warning(f"Question too short: {len(question)}")
        return False, "Question must be at least 3 characters long"
    
    if len(question.strip()) > 500:
        logger.warning(f"Question too long: {len(question)}")
        return False, "Question must be less than 500 characters"
    
    # Check for SQL injection attempts
    dangerous_patterns = ["DROP", "DELETE", "INSERT", "UPDATE", "UNION", "EXEC"]
    question_upper = question.upper()
    for pattern in dangerous_patterns:
        if pattern in question_upper:
            logger.warning(f"Suspected SQL injection: {pattern} in question")
            return False, "Invalid question pattern detected"
    
    return True, "Valid"

# ---------- SQL VALIDATION ----------
def is_safe(sql):
    """Validate SQL - only SELECT allowed"""
    if not sql or not isinstance(sql, str):
        return False
    
    sql_upper = sql.upper().strip()
    
    # 1. Must be SELECT only
    if not sql_upper.startswith("SELECT"):
        return False
    
    # 2. Block dangerous keywords
    dangerous = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
        "EXEC", "EXECUTE", "XP_", "SP_", 
        "GRANT", "REVOKE", "SHUTDOWN"
    ]
    
    for keyword in dangerous:
        if keyword in sql_upper:
            return False
    
    # 3. Block system tables
    system_tables = ["SQLITE_MASTER", "SQLITE_TEMP_MASTER"]
    for table in system_tables:
        if table in sql_upper:
            return False
    
    return True

# ---------- EXECUTE SQL ----------
def run_sql(sql):
    """Execute SQL with error handling"""
    try:
        conn = sqlite3.connect("clinic.db")
        cur = conn.cursor()
        cur.execute(sql)

        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        conn.close()
        
        return cols, rows
    
    except sqlite3.DatabaseError as e:
        raise Exception(f"Database Error: {str(e)}")
    except sqlite3.OperationalError as e:
        raise Exception(f"SQL Syntax Error: {str(e)}")
    except Exception as e:
        raise Exception(f"Query Failed: {str(e)}")

# ---------- FALLBACK SQL MAPPER ----------
fallback_queries = {
    "how many patients": "SELECT COUNT(*) as total_patients FROM patients",
    "how many female": "SELECT COUNT(*) as female_patients FROM patients WHERE gender='F'",
    "how many male": "SELECT COUNT(*) as male_patients FROM patients WHERE gender='M'",
    "list patients": "SELECT first_name, last_name, email, city FROM patients LIMIT 20",
    "all patients": "SELECT * FROM patients LIMIT 20",
    "show patients": "SELECT first_name, last_name, email, city FROM patients LIMIT 20",
    "list patients in hyderabad": "SELECT first_name, last_name, email, phone FROM patients WHERE city='Hyderabad'",
    "how many doctors": "SELECT COUNT(*) as total_doctors FROM doctors",
    "list doctors": "SELECT name, specialization, department FROM doctors",
    "show doctors": "SELECT name, department, specialization FROM doctors",
    "all doctors": "SELECT * FROM doctors",
    "cardiology doctors": "SELECT name, specialization, department FROM doctors WHERE specialization='Cardiology'",
    "busiest doctor": "SELECT d.name, COUNT(a.id) as appointment_count FROM doctors d JOIN appointments a ON d.id=a.doctor_id GROUP BY d.id ORDER BY COUNT(a.id) DESC LIMIT 1",
    "total revenue": "SELECT SUM(total_amount) as total_revenue FROM invoices",
    "unpaid invoices": "SELECT * FROM invoices WHERE status!='Paid' LIMIT 10",
    "all invoices": "SELECT * FROM invoices LIMIT 20",
    "show invoices": "SELECT * FROM invoices LIMIT 20",
    "top 5 patients": "SELECT p.first_name, p.last_name, SUM(i.total_amount) as total_amount FROM patients p JOIN invoices i ON p.id=i.patient_id GROUP BY p.id ORDER BY SUM(i.total_amount) DESC LIMIT 5",
    "appointments by status": "SELECT status, COUNT(*) as count FROM appointments GROUP BY status",
    "show appointments": "SELECT * FROM appointments LIMIT 20",
    "all appointments": "SELECT * FROM appointments LIMIT 20",
    "list appointments": "SELECT * FROM appointments LIMIT 20",
}

def get_fallback_sql(question):
    """Try to match question to fallback queries"""
    q_lower = question.lower().strip()

    # Try exact substring matches first
    for key, sql in fallback_queries.items():
        if key in q_lower:
            print(f"[FALLBACK] Matched '{key}' in '{q_lower}'")
            return sql

    print(f"[FALLBACK] No match for: {q_lower}")
    print(f"[FALLBACK] Available keys: {list(fallback_queries.keys())}")
    return None

# ---------- ADVANCED CHART GENERATOR ----------
def create_chart(cols, rows):
    """Create Plotly charts based on data structure"""
    if not rows or not cols or len(rows) == 0:
        logger.info("No rows to chart")
        return None

    try:
        # Single row data - no chart
        if len(rows) == 1:
            logger.info("Single row - no chart generated")
            return None

        # Two columns - Bar or Line chart
        if len(cols) == 2:
            labels = [str(row[0]) for row in rows]
            values = [float(row[1]) if isinstance(row[1], (int, float)) else row[1] for row in rows]

            # Bar chart for categorical data
            fig = go.Figure(data=[go.Bar(
                x=labels, 
                y=values,
                marker=dict(color='rgba(102, 126, 234, 0.7)')
            )])
            fig.update_layout(
                title=f"{cols[0]} vs {cols[1]}",
                xaxis_title=cols[0],
                yaxis_title=cols[1],
                height=400,
                template="plotly_white"
            )
            logger.info(f"Generated bar chart for 2 columns: {cols}")
            return fig.to_html(include_plotlyjs='cdn')

        # Three columns - could be time series or grouped bar
        if len(cols) == 3:
            # Try to detect date column
            first_vals = [str(row[0]) for row in rows]
            if any(c in first_vals[0].lower() for c in ['-', '/', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                # Time series
                x_vals = [str(row[0]) for row in rows]
                y_vals = [float(row[1]) if isinstance(row[1], (int, float)) else 0 for row in rows]
                
                fig = go.Figure(data=[go.Scatter(
                    x=x_vals, 
                    y=y_vals,
                    mode='lines+markers',
                    line=dict(color='rgba(102, 126, 234, 1)', width=2)
                )])
                fig.update_layout(
                    title="Time Series Trend",
                    xaxis_title=cols[0],
                    yaxis_title=cols[1],
                    height=400,
                    template="plotly_white"
                )
                logger.info("Generated time series chart")
                return fig.to_html(include_plotlyjs='cdn')

        # Default: no chart for complex data
        logger.info(f"Complex data ({len(cols)} columns) - returning table only")
        return None

    except Exception as e:
        logger.error(f"Chart generation error: {str(e)}")
        return None

# ---------- HEALTH ----------
@app.get("/health")
def health():
    logger.info("Health check requested")
    return {
        "status": "ok",
        "database": "connected",
        "cache_size": len(query_cache),
        "timestamp": datetime.now().isoformat()
    }

# ---------- CHAT ----------
@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Convert natural language question to SQL and return results
    
    Features:
    - Input validation
    - Query caching (1 hour TTL)
    - Rate limiting (10 req/min)
    - Comprehensive logging
    - Advanced visualization
    """
    logger.info(f"NEW REQUEST: {req.question[:100]}")
    
    # 1. INPUT VALIDATION
    is_valid, error_msg = validate_input(req.question)
    if not is_valid:
        logger.error(f"Input validation failed: {error_msg}")
        return {
            "message": f"❌ Input Validation Error: {error_msg}",
            "sql_query": "",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "chart": None,
            "mode": "validation_error"
        }
    
    # 2. RATE LIMITING
    if not check_rate_limit():
        logger.error("Rate limit exceeded")
        return {
            "message": "❌ Rate Limit Exceeded: Too many requests. Please wait a moment.",
            "sql_query": "",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "chart": None,
            "mode": "rate_limited"
        }
    
    # 3. QUERY CACHING
    cached_result = cache_get(req.question)
    if cached_result:
        logger.info(f"Returning CACHED result for: {req.question[:50]}")
        cached_result["from_cache"] = True
        return cached_result

    # simple context with schema info
    from vanna_setup import get_schema_for_llm
    
    schema = get_schema_for_llm()
    
    class Ctx:
        metadata = {
            "db_type": "sqlite",
            "database": "clinic.db",
            "schema": schema
        }

    sql = ""
    full_text = ""
    
    # APPROACH: Try fallback FIRST to avoid hitting rate limits
    fallback_sql = get_fallback_sql(req.question)
    if fallback_sql:
        sql = fallback_sql
        full_text = "[Fallback] Matched"
        logger.info(f"Using fallback: {sql[:50]}")
    else:
        # Only try Groq if no fallback match
        try:
            # Add schema to question for better LLM understanding
            question_with_schema = f"{req.question}\n\nDatabase Schema:\n{schema}"
            
            logger.info(f"Sending to Vanna Agent: {req.question[:50]}")
            # ask agent with context and schema
            res = agent.send_message(message=question_with_schema, request_context=Ctx())

            async for r in res:
                full_text += str(r)

            # Try multiple ways to extract SQL
            sql = ""
            
            # Method 1: Look for ```sql blocks
            if "```sql" in full_text:
                start = full_text.find("```sql") + 6
                end = full_text.find("```", start)
                sql = full_text[start:end].strip()
            # Method 2: Look for SELECT
            elif "SELECT" in full_text.upper():
                start_idx = full_text.upper().find("SELECT")
                sql = full_text[start_idx:].split(';')[0].strip()
            
            if sql:
                logger.info(f"SQL extracted: {sql[:100]}")
            else:
                logger.warning(f"No SQL found in response")

        except Exception as e:
            # If API fails, error already logged above
            logger.error(f"Agent error: {str(e)}")

    # Try fallback if SQL is empty
    if not sql:
        sql = get_fallback_sql(req.question)
        if sql:
            full_text = f"[Fallback] Matched to: {sql}"
            logger.info(f"Using fallback SQL: {sql[:50]}")

    # safety check
    if not sql:
        error_msg = "No SQL query generated"
        logger.error(error_msg)
        return {
            "message": f"❌ SQL Validation Failed: {error_msg}",
            "sql_query": "",
            "agent_response": full_text[:500] if full_text else "[Empty response]",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "chart": None,
            "mode": "fallback" if (full_text and "Fallback" in full_text) else "agent"
        }
    
    if not is_safe(sql):
        logger.warning(f"SQL validation failed for: {sql[:100]}")
        return {
            "message": "❌ SQL Validation Failed: Query contains dangerous keywords or operations (only SELECT allowed)",
            "sql_query": sql,
            "agent_response": full_text[:500] if full_text else "[Empty response]",
            "columns": [],
            "rows": [],
            "row_count": 0,
            "chart": None,
            "mode": "fallback" if (full_text and "Fallback" in full_text) else "agent"
        }

    # run query
    try:
        logger.info(f"Executing SQL: {sql[:100]}")
        cols, rows = run_sql(sql)
        logger.info(f"Query executed: {len(rows)} rows returned")

        # Check for empty results
        if not rows or len(rows) == 0:
            result = {
                "message": "✓ Query executed but no data found",
                "sql_query": sql,
                "columns": cols,
                "rows": [],
                "row_count": 0,
                "chart": None,
                "mode": "fallback" if "Fallback" in full_text else "agent",
                "from_cache": False
            }
            logger.info("Query returned no rows")
            cache_set(req.question, result)
            return result

        chart_html = create_chart(cols, rows)

        result = {
            "message": f"✓ {len(rows)} rows found",
            "sql_query": sql,
            "columns": cols,
            "rows": rows,
            "row_count": len(rows),
            "chart": chart_html,
            "mode": "fallback" if "Fallback" in full_text else "agent",
            "from_cache": False
        }
        
        # Cache successful results
        logger.info(f"Caching result for: {req.question[:50]}")
        cache_set(req.question, result)
        
        return result

    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {
            "message": f"❌ Database Error: {str(e)}",
            "sql_query": sql,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "chart": None,
            "mode": "fallback" if "Fallback" in full_text else "agent"
        }