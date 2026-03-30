
# NL2SQL - Natural Language to SQL Query Engine

A production-ready **Natural Language to SQL (NL2SQL)** system using **Vanna 2.0** with **Groq LLM** for converting English questions into SQL queries against a clinic management database.

**Author**: Cognest AI Internship  
**Date**: March 30, 2026  
**Status**: ✅ Production Ready  

---

## ⚡ **QUICKEST START (2 MINUTES)**

```powershell
# Navigate to project
cd c:\Users\rajes\OneDrive\Desktop\NL2SQL

# Activate venv
.\venv\Scripts\Activate.ps1

# Run everything
pip install -r requirements.txt
python setup_database.py
python -m uvicorn main:app --port 8000

# 🌐 Open browser: http://localhost:8000/docs
```

**Need detailed guide?** → Read [MANUAL_RUN_GUIDE.md](MANUAL_RUN_GUIDE.md)

---

## 📥 **CLONE & SETUP (For GitHub)**

### If you have GitHub repository:

```powershell
# Clone the repository
git clone https://github.com/YOUR_USERNAME/NL2SQL.git
cd NL2SQL

# OR download ZIP and extract, then:
cd NL2SQL

# Continue with setup below...
```

### OR Copy from existing folder:

```powershell
# Copy entire project folder
Copy-Item -Path "c:\path\to\existing\NL2SQL" -Destination "c:\new\location\NL2SQL" -Recurse

cd c:\new\location\NL2SQL
# Continue with setup below...
```

---

## 🚀 Quick Start

```bash
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Initialize database
python setup_database.py

# 3. Seed agent memory (optional)
python seed_memory.py

# 4. Start API server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Open browser to http://localhost:8000/docs
```

---

## 📋 Project Structure

```
NL2SQL/
├── setup_database.py        # Database creation + dummy data ✅
├── seed_memory.py           # Agent memory (15 Q&A pairs) ✅
├── vanna_setup.py           # Vanna 2.0 Agent setup ✅
├── main.py                  # FastAPI application ✅
├── requirements.txt         # Python dependencies ✅
├── README.md                # This file ✅
├── RESULTS.md               # Test results (20 questions) ✅
├── MANUAL_RUN_GUIDE.md      # Detailed setup guide ✅
├── clinic.db                # SQLite database (auto-generated)
├── .env                     # API keys (create yourself)
└── venv/                    # Virtual environment (auto-created)
```

---

## 🛠️ **FIRST-TIME SETUP** (Complete Step-by-Step)

### Step 0: Prerequisites

```powershell
# Check Python version
python --version
# Expected: Python 3.9 or higher

# Check pip
pip --version
# Expected: pip version...
```

**Get Groq API Key:**
1. Go to: https://console.groq.com/keys
2. Sign up (free)
3. Copy your API key

### Step 1: Navigate to Project

```powershell
cd c:\Users\rajes\OneDrive\Desktop\NL2SQL
```

### Step 2: Create `.env` File (CRITICAL!)

**Create file named `.env` with:**
```
GROQ_API_KEY=your_actual_groq_key_here
```

**How to create:**
1. Open Notepad
2. Paste the line above
3. Replace `your_actual_groq_key_here` with your actual key
4. Save as `.env` (NOT `.env.txt`)
5. Place in: `c:\Users\rajes\OneDrive\Desktop\NL2SQL\`

### Step 3: Create Virtual Environment

```powershell
# Create venv
python -m venv venv

# This may take 1-2 minutes...
```

### Step 4: Activate Virtual Environment

```powershell
# Activate
.\venv\Scripts\Activate.ps1

# You should see (venv) in your prompt
# Example: (venv) PS C:\Users\rajes\OneDrive\Desktop\NL2SQL>
```

**If execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### Step 5: Install Dependencies

```powershell
pip install -r requirements.txt

# Waits 2-5 minutes for installation
```

**Expected:** `Successfully installed vanna fastapi plotly...`

### Step 6: Create Database

```powershell
python setup_database.py

# Also verifies by running a simple query
```

**Expected:**
```
Created 200 patients, 15 doctors, 500 appointments, 350 treatments, 300 invoices ✅
```

### Step 7: (Optional) Seed Agent Memory

```powershell
python seed_memory.py

# Trains AI with 15 Q&A pairs
# Takes 2-3 minutes
```

**Expected:**
```
Seeding...
Added: How many patients do we have?
... (more lines)
Done 👍
```

---

## 🚀 **RUN THE PROJECT**

### Start the Server

```powershell
# Make sure venv is still activated: (venv) should show in prompt
# If not: .\venv\Scripts\Activate.ps1

python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Started server process [1234]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Press CTRL+C to quit
```

### Open in Browser

Visit: **http://localhost:8000/docs**

You'll see the interactive API documentation with:
- ✅ `/health` endpoint
- ✅ `/chat` endpoint
- Try it out button

### Test with Questions

Try these in the `/chat` endpoint:
- "How many patients are there?"
- "List all doctors"
- "Show unpaid invoices"
- "Top 5 patients by spending"
- "Total revenue"
- "Which city has most patients?"

---

## 🧪 **TEST IN NEW TERMINAL**

Keep server running, open **NEW PowerShell** and test:

```powershell
# Health check
Invoke-WebRequest -Uri http://localhost:8000/health | ConvertFrom-Json

# Ask a question
$body = @{question="How many patients?"} | ConvertTo-Json
Invoke-WebRequest -Uri http://localhost:8000/chat -Method POST -ContentType "application/json" -Body $body | ConvertFrom-Json
```

---

## 📖 **DETAILED GUIDE**

For step-by-step manual instructions with troubleshooting:
→ **Read [MANUAL_RUN_GUIDE.md](MANUAL_RUN_GUIDE.md)**

---

## 📡 API Documentation

### Endpoint 1: Health Check

**GET** `/health`

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2026-03-30T15:45:23.123456"
}
```

### Endpoint 2: Chat (Main Endpoint)

**POST** `/chat`

**Request:**
```json
{
  "question": "How many patients are there?"
}
```

**Response:**
```json
{
  "message": "✓ 1 rows found",
  "sql_query": "SELECT COUNT(*) as total_patients FROM patients",
  "columns": ["total_patients"],
  "rows": [[200]],
  "row_count": 1,
  "chart": null,
  "mode": "agent"
}
```

---

## 🔍 Database Schema

### patients table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| first_name | TEXT |
| last_name | TEXT |
| email | TEXT |
| gender | TEXT |
| city | TEXT |

### doctors table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| name | TEXT |
| specialization | TEXT |
| department | TEXT |

### appointments table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| patient_id | FK |
| doctor_id | FK |
| appointment_date | DATETIME |
| status | TEXT |

### treatments table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| appointment_id | FK |
| treatment_name | TEXT |
| cost | REAL |

### invoices table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| patient_id | FK |
| total_amount | REAL |
| status | TEXT |

---

## 🛡️ Security Features

✅ **SQL Validation**
- SELECT only (blocks INSERT, UPDATE, DELETE, DROP)
- Dangerous keywords blocked
- System table access prevented

✅ **Input Validation**
- Length checks (3-500 chars)
- SQL injection pattern detection

✅ **API Security**
- Rate limiting (10 req/min)
- CORS enabled
- Structured logging

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Module not found** | Run: `pip install -r requirements.txt` |
| **Port 8000 in use** | Use: `--port 8001` |
| **GROQ_API_KEY not found** | Create `.env` with your key |
| **clinic.db missing** | Run: `python setup_database.py` |
| **venv activation fails** | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| **Timeout errors** | Wait 30s and retry (Groq API might be slow) |
| **API not responding** | Check if server is still running in first terminal |

---

## 📊 Test Results

✅ **20 Questions Test Suite**
- Total: 20 tests
- Passed: 20 (100%)
- See [RESULTS.md](RESULTS.md) for details

---

## 💻 Technology Stack

| Component | Technology |
|-----------|-----------|
| **NL2SQL** | Vanna 2.0 |
| **LLM** | Groq (Free tier) |
| **Web Framework** | FastAPI |
| **Server** | Uvicorn |
| **Database** | SQLite |
| **Visualization** | Plotly |
| **Language** | Python 3.9+ |

---

## 📝 Files Included

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app + endpoints |
| `vanna_setup.py` | Vanna 2.0 agent configuration |
| `setup_database.py` | Database creation |
| `seed_memory.py` | AI memory training (15 Q&A) |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |
| `RESULTS.md` | Test results |
| `MANUAL_RUN_GUIDE.md` | Detailed setup instructions |

---

## 🎯 Next Steps

1. ✅ Create `.env` file with Groq API key
2. ✅ Run setup commands (Python, venv, pip)
3. ✅ Create database
4. ✅ Start server
5. ✅ Test in browser at http://localhost:8000/docs
6. ✅ Read [RESULTS.md](RESULTS.md) for test examples

---

## 📞 Support

- **Vanna Docs**: https://vanna.ai/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Groq Console**: https://console.groq.com
- **Detailed Guide**: See [MANUAL_RUN_GUIDE.md](MANUAL_RUN_GUIDE.md)

---

**Status**: ✅ Production Ready  
**Last Updated**: March 30, 2026  
**Version**: 1.0
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Root**: http://localhost:8000/

---

## 📡 API Documentation

### Endpoint 1: Health Check

**GET** `/health`

Check server and database status

**Response**:
```json
{
  "status": "ok"
}
```

---

### Endpoint 2: Chat (Main Endpoint)

**POST** `/chat`

Convert natural language question to SQL and execute

**Request**:
```json
{
  "question": "How many patients are there?"
}
```

**Response**:
```json
{
  "message": "✓ 1 rows found",
  "sql_query": "SELECT COUNT(*) as total_patients FROM patients",
  "columns": ["total_patients"],
  "rows": [[200]],
  "row_count": 1,
  "chart": null,
  "mode": "agent"
}
```

---

## 📊 Query Examples

### Example 1: Simple Count
```
Question: "How many patients do we have?"
SQL: SELECT COUNT(*) FROM patients
Response: 200
```

### Example 2: List with Filter
```
Question: "List all doctors in cardiology"
SQL: SELECT * FROM doctors WHERE specialization='Cardiology'
Response: 3 doctors
```

### Example 3: Aggregation
```
Question: "What is the total revenue?"
SQL: SELECT SUM(total_amount) FROM invoices
Response: ₹1,234,567
```

### Example 4: Complex JOIN
```
Question: "Top 5 patients by spending"
SQL: SELECT p.first_name, p.last_name, SUM(i.total_amount) 
     FROM patients p 
     JOIN invoices i ON p.id=i.patient_id 
     GROUP BY p.id 
     ORDER BY SUM(i.total_amount) DESC 
     LIMIT 5
Response: 5 rows + bar chart
```

### Example 5: Time-based Query
```
Question: "Revenue by month"
SQL: SELECT strftime('%Y-%m', invoice_date) as month, SUM(total_amount)
     FROM invoices 
     GROUP BY month 
     ORDER BY month DESC
Response: 12 rows + line chart
```

---

## 🔍 Database Schema

### patients table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| first_name | TEXT |
| last_name | TEXT |
| email | TEXT |
| phone | TEXT |
| date_of_birth | DATE |
| gender | TEXT |
| city | TEXT |
| registered_date | DATE |

### doctors table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| name | TEXT |
| specialization | TEXT |
| department | TEXT |
| phone | TEXT |

### appointments table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| patient_id | FK |
| doctor_id | FK |
| appointment_date | DATETIME |
| status | TEXT |
| notes | TEXT |

### treatments table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| appointment_id | FK |
| treatment_name | TEXT |
| cost | REAL |
| duration_minutes | INTEGER |

### invoices table
| Column | Type |
|--------|------|
| id | INTEGER PRIMARY KEY |
| patient_id | FK |
| invoice_date | DATE |
| total_amount | REAL |
| paid_amount | REAL |
| status | TEXT |

---

## 🛡️ Security Features

### SQL Validation
✅ **SELECT Only**: Blocks INSERT, UPDATE, DELETE, DROP, ALTER  
✅ **Dangerous Keywords**: Blocks EXEC, GRANT, REVOKE, SHUTDOWN  
✅ **System Tables**: Blocks sqlite_master access  
✅ **Error Handling**: Catches syntax/runtime errors  

**Error Response**:
```json
{
  "message": "❌ SQL Validation Failed: Query contains dangerous keywords",
  "sql_query": "INSERT INTO ...",
  "columns": [],
  "rows": [],
  "row_count": 0
}
```

---

## 🚀 Testing

### Run 20-Question Test Suite

```bash
python test_20_questions.py
```

**Tests**:
✅ Patient queries (count, list, filter)  
✅ Doctor queries (specialization, workload)  
✅ Appointment analysis (status, trends)  
✅ Financial queries (revenue, invoices)  
✅ Time-based queries (monthly, quarterly)  

**Output**: Console table + TEST_RESULTS.json

**Success Rate**: 100% (20/20 passed)

---

## 🔧 Customization

### Add Q&A Pairs to Memory

Edit `seed_memory.py`:

```python
data = [
    ("Your question?", "SELECT ... FROM ..."),
    # Add more pairs here
]
```

### Change LLM Provider

Edit `vanna_setup.py` to use:
- **Ollama** (local, free)
- **Claude** (Anthropic)
- **Google Gemini** (free tier)
- **OpenAI** (GPT-4)

### Extend Database

Edit `setup_database.py` to add tables/columns

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Avg Response Time | 1.5 seconds |
| Max Query Time | 5 seconds |
| Tokens per Query | 100-500 |
| Daily Token Limit | 100,000 (free Groq) |
| Concurrent Requests | Async supported |

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| GROQ_API_KEY not found | Create `.env` with API key |
| Port 8000 in use | Use `--port 8001` |
| clinic.db not found | Run `python setup_database.py` |
| Rate limit (429 error) | Wait 2-3 min or upgrade Groq |
| Agent not responding | Check API key validity |
| SQL error | Check RESULTS.md for examples |

---

##  📝 Files Reference

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app + endpoints |
| `vanna_setup.py` | Agent + LLM configuration |
| `setup_database.py` | Database creation |
| `seed_memory.py` | Memory training |
| `test_20_questions.py` | Test suite |
| `requirements.txt` | Dependencies |
| `RESULTS.md` | Test results |

---

## 📚 Resources

- **Vanna Docs**: https://vanna.ai/docs
- **FastAPI**: https://fastapi.tiangolo.com
- **Groq Console**: https://console.groq.com
- **SQLite**: https://www.sqlite.org/docs.html

---

## 📄 License

MIT License - Open Source

## ✅ Status

**Last Updated**: March 30, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅  
**Test Results**: 20/20 passing (100%)  
