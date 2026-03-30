# Healthcare Intelligence: NL2SQL Bot (Vanna 2.0 + Groq)

A production-ready Natural Language to SQL (NL2SQL) system for clinic management data, built for the AI/ML Developer Internship Technical Screening.

## 🚀 Overview
This system converts plain English questions into secure SQLite queries using **Vanna AI 2.0**, **FastAPI**, and **Groq (Llama 3.1)**. It features a robust multi-layer query resolution engine, automated data visualization (Plotly), and integrated safety validation.

### Key Features
- **Vanna 2.0 Agent Architecture**: Uses `DemoAgentMemory`, `SqliteRunner`, and `ToolRegistry`.
- **Intelligent Fallback Layer**: Recognizes common patterns for ultra-fast, zero-latency responses.
- **Auto-Visualization**: Automatically returns Plotly JSON for charts (bar/line) based on result structure.
- **SQL Security**: Rigorous validation layer blocks dangerous operations (only `SELECT` allowed).

---

## 🛠️ Setup Instructions

### 1. Requirements
Ensure you have **Python 3.10+** installed.

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_gsk_apikey_here
```

### 3. Installation
```bash
pip install -r requirements.txt
```

### 4. Database Initialization
Create the database and insert 500+ records of realistic dummy data:
```bash
python setup_database.py
```

### 5. Seeding Memory
Train the agent with 15 initial Q&A pairs to guide the reasoning:
```bash
python seed_memory.py
```

### 6. Run the API Server
Start the FastAPI backend with Uvicorn:
```bash
uvicorn main:app --port 8000
```

---

## 🌐 API Documentation

### POST `/chat`
Generates SQL from natural language and returns data with charts.

**Request Body:**
```json
{ "question": "Show me total revenue by doctor" }
```

**Response Body:**
```json
{
  "status": "success",
  "message": "...",
  "sql_query": "SELECT ...",
  "columns": ["doctor_name", "total_revenue"],
  "rows": [["Dr. Smith", 5000], ["Dr. Doe", 3200]],
  "chart": { "data": [...], "layout": {...} },
  "chart_type": "bar"
}
```

### GET `/health`
Returns system status and agent memory metrics.

---

## 🏗️ Architecture
1. **User Question** reaches FastAPI endpoint.
2. **Fallback Engine** checks for manual patterns.
3. **Vanna 2.0 Agent** (if no fallback) generates SQL using Groq Llama 3.1 + Schema memory.
4. **Validation Layer** ensures SQL is safe (SELECT only).
5. **SqliteRunner** executes query against `clinic.db`.
6. **Analytics Layer** suggests chart types and generates Plotly JSON.

---

## 📊 Results Summary
For the 20 test questions required by Step 9, see [RESULTS.md](./RESULTS.md).
Current test coverage: **18/20 questions producing correct SQL**.
