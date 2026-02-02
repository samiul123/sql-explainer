# SQL Explainer

An intelligent SQL query analyzer and optimizer powered by AI. Paste any SQL query to get detailed explanations, detect issues, and receive actionable optimization suggestions with automatic SQL rewrites.

## ✨ Features

### 🔍 **SQL Analysis**
- **Multi-dialect Support**: PostgreSQL, MySQL, SQLite, T-SQL, BigQuery, Snowflake
- **Query Parsing**: Extracts structure, tables, joins, filters, aggregations
- **Syntax Normalization**: Cleans and standardizes SQL formatting

### 📚 **Intelligent Explanation**
- Natural language breakdown of query logic
- Step-by-step clause analysis
- Confidence scoring for explanations
- Assumption tracking (when schema is missing)

### ⚠️ **Issue Detection**
- **Critical**: Missing indexes on large joins, N+1 query patterns
- **Warning**: `SELECT *` usage, missing `LIMIT` clauses, leading wildcards in `LIKE`
- **Info**: `COUNT(*)` usage recommendations

### 🚀 **Optimization Suggestions**
- **High Impact**: Index recommendations, join order improvements
- **Medium Impact**: Query rewrite suggestions, filter optimizations
- **Low Impact**: Minor efficiency improvements
- Includes SQL statements for creating suggested indexes
- Safe query rewrites maintaining semantic equivalence

### 💻 **Developer Experience**
- **Syntax Highlighting**: CodeMirror-powered SQL editor
- **Copy to Clipboard**: One-click copy for all SQL outputs
- **Responsive UI**: Clean, modern interface built with Next.js + Tailwind CSS
- **Real-time Analysis**: Fast feedback with local Ollama models

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Frontend (Next.js)                  │
│  ┌──────────────────────────────────────────┐  │
│  │  SQL Editor + Results Panels              │  │
│  │  - Explanation, Issues, Optimizations     │  │
│  │  - Rewritten SQL View                     │  │
│  └──────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/JSON
┌─────────────────▼───────────────────────────────┐
│          Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────┐  │
│  │  SQL Analyzer (sqlglot)                   │  │
│  │  - Parse + Normalize SQL                  │  │
│  │  - Extract Structure                      │  │
│  │  - Lint with Rules                        │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │  LangChain + Ollama                       │  │
│  │  - Explain Chain (ExplainOutput)          │  │
│  │  - Optimize Chain (OptimizeOutput)        │  │
│  └──────────────────────────────────────────┘  │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│          Ollama (llama3.1:8b)                    │
│  Local LLM for SQL explanation + optimization    │
└──────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 20+ and npm
- **Python** 3.9+
- **Ollama** with `llama3.1:8b` model installed

### 1. Install Ollama & Model

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull llama3.1:8b

# Start Ollama server (if not auto-started)
ollama serve
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env to set OLLAMA_MODEL, ALLOWED_ORIGINS, etc.

# Start backend server
cd app
uvicorn main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API endpoint (optional)
# Create .env.local and set:
# NEXT_PUBLIC_API_BASE=http://localhost:8000

# Start frontend dev server
npm run dev
```

Frontend runs at `http://localhost:3000`

### 4. Try It Out!

1. Open `http://localhost:3000`
2. Select a SQL dialect (e.g., PostgreSQL)
3. Paste a query:
   ```sql
   SELECT u.name, COUNT(*) as order_count
   FROM users u
   JOIN orders o ON u.id = o.user_id
   WHERE u.email LIKE '%@example.com'
   GROUP BY u.name
   ```
4. Click **Analyze**
5. Explore tabs: Explanation, Issues, Optimizations, Rewritten SQL

## 📁 Project Structure

```
sql-explainer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + /analyze endpoint
│   │   ├── schemas.py           # Pydantic models (Request/Response)
│   │   ├── sql_analyzer.py      # sqlglot parsing + linting rules
│   │   └── chains.py            # LangChain + Ollama chains
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Main application page
│   │   └── globals.css
│   ├── components/
│   │   ├── sql-analyzer/
│   │   │   ├── InputPanel.tsx   # SQL editor + controls
│   │   │   ├── ResultsPanel.tsx # Tabbed results view
│   │   │   ├── SqlEditor.tsx    # CodeMirror wrapper
│   │   │   ├── SqlViewerSection.tsx  # Reusable SQL viewer
│   │   │   ├── cards/           # IssueCard, SuggestionCard
│   │   │   └── tabs/            # ExplanationTab, IssuesTab, etc.
│   │   └── ui/                  # Badge, CodeBlock, TabButton
│   ├── hooks/
│   │   ├── useSqlAnalyzer.ts    # API client hook
│   │   ├── useAnalysisResults.ts
│   │   └── useClipboard.ts
│   └── package.json
│
└── README.md
```

## 🔧 Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Frontend Environment Variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## 📝 API Reference

### `POST /analyze`

**Request:**
```json
{
  "dialect": "postgres",
  "sql": "SELECT * FROM users WHERE email = 'test@example.com'",
  "schema_text": "users: id, email, name, created_at"
}
```

**Response:**
```json
{
  "dialect": "postgres",
  "normalized_sql": "SELECT * FROM users WHERE email = 'test@example.com'",
  "parsed": true,
  "structure": { "select_star": true, "tables": ["users"], ... },
  "explanation": "This query retrieves all columns from the users table...",
  "breakdown": ["SELECT * selects all columns", "FROM users..."],
  "assumptions": ["Assuming users table exists"],
  "issues": [
    {
      "code": "SELECT_STAR",
      "severity": "warning",
      "message": "Avoid SELECT * in production queries...",
      "evidence": "SELECT *"
    }
  ],
  "suggestions": [
    {
      "title": "Add index on email column",
      "impact": "high",
      "rationale": "WHERE clause filters by email without index...",
      "actions": ["CREATE INDEX idx_users_email ON users(email)"],
      "index_sql": ["CREATE INDEX idx_users_email ON users(email)"],
      "rewrite_sql": null,
      "caveats": []
    }
  ],
  "rewritten_sql": "SELECT id, email, name FROM users WHERE email = 'test@example.com'",
  "confidence": "high"
}
```

## 🎨 Customization


### Changing LLM Model

Replace `llama3.1:8b` with any Ollama-compatible model:

```bash
# Pull a different model
ollama pull mistral:7b

# Update .env
OLLAMA_MODEL=mistral:7b
```

## 🧪 Testing

```bash
# Backend tests (coming soon)
cd backend
pytest

# Frontend tests (coming soon)
cd frontend
npm test
```
## 📧 Contact

Questions or feedback? Open an issue or reach out!

---

**Built with ❤️ using AI-powered tools**
