#!/bin/bash
# Complete setup script - adds ALL missing files to your CorgiDemo folder

echo "🚀 ETF Compliance Workflow Engine - Complete Setup"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -d "src" ] || [ ! -d "database" ]; then
    echo "❌ Error: Please run this script from your CorgiDemo directory"
    echo ""
    echo "Usage:"
    echo "  cd ~/CorgiDemo"
    echo "  bash COMPLETE_SETUP.sh"
    echo ""
    exit 1
fi

echo "✅ Found CorgiDemo structure"
echo ""
echo "Adding missing files..."
echo ""

# ============================================================================
# 1. CREATE __init__.py FILES
# ============================================================================

echo "📦 Creating __init__.py files..."

cat > src/__init__.py << 'INITEOF'
"""ETF Compliance Workflow Engine."""

__version__ = "1.0.0"
INITEOF

cat > src/routes/__init__.py << 'INITEOF'
"""API routes package."""

from .filings import router as filings_router
from .audit import router as audit_router

__all__ = ['filings_router', 'audit_router']
INITEOF

cat > src/services/__init__.py << 'INITEOF'
"""Services package for ETF Compliance Engine."""

from .audit import AuditService
from .workflow import WorkflowEngine
from .validation import LLMValidator

__all__ = ['AuditService', 'WorkflowEngine', 'LLMValidator']
INITEOF

cat > src/utils/__init__.py << 'INITEOF'
"""Utils package."""

from .config import config

__all__ = ['config']
INITEOF

cat > tests/__init__.py << 'INITEOF'
"""Tests package for ETF Compliance Workflow Engine."""
INITEOF

echo "  ✅ src/__init__.py"
echo "  ✅ src/routes/__init__.py"
echo "  ✅ src/services/__init__.py"
echo "  ✅ src/utils/__init__.py"
echo "  ✅ tests/__init__.py"
echo ""

# ============================================================================
# 2. CREATE DOCUMENTATION FILES
# ============================================================================

echo "📄 Creating documentation files..."

cat > README.md << 'READMEEOF'
# ETF Compliance Workflow Engine

A lightweight system for managing regulatory filing workflows with built-in auditability and AI-assisted validation.

## 🎯 Purpose

This system demonstrates how to turn manual ETF compliance workflows into structured, auditable software. It shows:

1. **State machine enforcement** for regulatory approval flows
2. **Immutable audit trails** for SEC compliance
3. **AI-assisted validation** that augments (not replaces) human judgment
4. **Version control** for filing lineage

---

## 🏗️ Architecture Decisions

### 1. State Machine Workflow Enforcement

ETF filings must follow strict approval workflows mandated by SEC regulations. This system enforces valid state transitions:

```
DRAFT → PENDING_REVIEW → APPROVED (terminal)
                      ↓
                   REJECTED → DRAFT (revise & resubmit)
```

**Why this matters:**
- Prevents invalid workflow shortcuts (e.g., DRAFT → APPROVED without review)
- Ensures every filing goes through proper approval chain
- Logs every transition with timestamp + actor for audit trail

**Implementation:** `src/services/workflow.py`

### 2. Immutable Audit Trail

Every action on a filing is recorded in the `audit_log` table:

- **Who**: Actor (user email/ID)
- **What**: Action performed (created, submitted, approved, rejected)
- **When**: Timestamp (UTC)
- **Why**: Metadata (comments, validation results)

**Why this matters:**
- SEC expects complete chain of custody for regulatory filings
- Audit entries are never updated or deleted (append-only)
- Enables compliance reporting and investigations

**Implementation:** `src/services/audit.py`

### 3. AI-Assisted Validation

Two-layer validation approach:

**Layer 1: Hard Rules** (blocking)
- Required fields check (e.g., series_id, reporting_period_end)
- Data type validation
- Value constraints (e.g., total_assets > 0)

**Layer 2: AI Quality Check** (warnings only)
- Numeric reasonableness (e.g., "holdings sum differs from total assets")
- Data consistency (e.g., "reporting period seems old")
- Missing context suggestions

**Why this matters:**
- Shows how LLMs can **augment** compliance workflows without replacing human oversight
- Hard rules block submission; AI warnings inform review
- Compliance officers maintain final judgment

**Implementation:** `src/services/validation.py`

### 4. Version Control

Filing revisions create a new record with:
- `parent_filing_id` → references previous version
- `version` → increments from parent
- New status: `DRAFT` (requires re-approval)

**Why this matters:**
- Approved filings are immutable (can't edit after SEC submission)
- Full history chain preserved for compliance
- Easy rollback or comparison between versions

---

## 🚀 Setup & Usage

### Prerequisites

- Python 3.9+
- (Optional) Anthropic API key for AI validation

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# (Optional) Configure API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Run Locally

```bash
# Initialize database (run once)
python -m src.database

# Start server
python -m src.main

# Server will run at http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## 📝 API Examples

### 1. Create Filing

```bash
curl -X POST http://localhost:8000/filings \
  -H "Content-Type: application/json" \
  -d '{
    "filing_name": "Q1 2025 Holdings Report",
    "filing_type": "N-PORT",
    "content": {
      "fund_name": "Corgi Innovation ETF",
      "series_id": "S000067890",
      "reporting_period_end": "2025-03-31",
      "total_assets": 250000000,
      "holdings": [
        {"ticker": "NVDA", "shares": 5000, "value": 4250000}
      ]
    },
    "created_by": "john.doe@corgi.com"
  }'
```

### 2. Submit for Review

```bash
curl -X POST http://localhost:8000/filings/1/submit \
  -H "Content-Type: application/json" \
  -d '{"actor": "john.doe@corgi.com"}'
```

### 3. Approve Filing

```bash
curl -X POST http://localhost:8000/filings/1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "reviewer": "jane.smith@corgi.com",
    "comments": "All holdings reconciled. Approved for submission."
  }'
```

### 4. Get Audit Trail

```bash
curl http://localhost:8000/filings/1/history
```

---

## 🏭 Production Considerations

### Security
- [ ] Add authentication/authorization (OAuth2, API keys)
- [ ] Implement role-based access control (RBAC)
- [ ] Rate limiting on API endpoints
- [ ] Input sanitization

### Database
- [ ] Migrate to PostgreSQL with replication
- [ ] Add connection pooling
- [ ] Implement backup/restore
- [ ] Database migrations (Alembic)

### Reliability
- [ ] Retry logic for AI validation
- [ ] Circuit breaker for external APIs
- [ ] Structured logging
- [ ] Monitoring and alerting

### Workflow
- [ ] Role-based approval routing
- [ ] Webhook notifications
- [ ] Email alerts for pending approvals
- [ ] Configurable approval requirements

---

## 📂 Project Structure

```
etf-compliance-engine/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Configuration template
├── database/
│   ├── schema.sql              # Database schema
│   └── seed.sql                # Sample data
├── src/
│   ├── main.py                 # FastAPI app entry
│   ├── models.py               # Pydantic models
│   ├── database.py             # SQLite utilities
│   ├── routes/
│   │   ├── filings.py          # Filing CRUD + workflow
│   │   └── audit.py            # Audit log queries
│   ├── services/
│   │   ├── workflow.py         # State machine
│   │   ├── validation.py       # AI validation
│   │   └── audit.py            # Audit service
│   └── utils/
│       └── config.py           # App config
├── tests/
│   ├── test_workflow.py
│   └── test_validation.py
└── examples/
    ├── sample_filing.json      # Example payloads
    └── postman_collection.json # API testing
```

---

## 🎓 Key Takeaways

This architecture demonstrates:

1. **Regulated Workflow Thinking** - State machines enforce compliance, every action is traceable
2. **Backend Architecture** - Type-safe API, separation of concerns, proper error handling
3. **Observability** - Complete audit trail, chain of custody verification
4. **AI Integration** - Thoughtful LLM use (augment, not replace), graceful degradation

Real-world applications: ETF/fund compliance, financial reporting, document management, change control systems.

---

## 📄 License

MIT License
READMEEOF

cat > QUICKSTART.md << 'QUICKEOF'
# Quick Start Guide

Get running in 5 minutes.

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Configure API key for AI validation
cp .env.example .env
# Edit .env and add ANTHROPIC_API_KEY

# 3. Initialize database
python -m src.database

# 4. Start server
python -m src.main
```

Server runs at: http://localhost:8000  
Docs: http://localhost:8000/docs

## Quick Test

### Option 1: Browser (Easiest)

1. Open http://localhost:8000/docs
2. Try "Create Filing" with:

```json
{
  "filing_name": "Test Filing",
  "filing_type": "N-PORT",
  "content": {
    "fund_name": "Test ETF",
    "series_id": "S000012345",
    "reporting_period_end": "2025-03-31",
    "total_assets": 100000000,
    "holdings": [
      {"ticker": "AAPL", "shares": 1000, "value": 185000}
    ]
  },
  "created_by": "test@example.com"
}
```

### Option 2: Command Line

```bash
# Create filing
curl -X POST http://localhost:8000/filings \
  -H "Content-Type: application/json" \
  -d '{
    "filing_name": "Q1 2025 Report",
    "filing_type": "N-PORT",
    "content": {
      "fund_name": "Test ETF",
      "series_id": "S000012345",
      "reporting_period_end": "2025-03-31",
      "total_assets": 100000000,
      "holdings": [{"ticker": "AAPL", "shares": 1000, "value": 185000}]
    },
    "created_by": "test@example.com"
  }'
```

## Troubleshooting

**"Module not found"**: `pip install -r requirements.txt`  
**"Database not found"**: `python -m src.database`  
**"Port in use"**: `PORT=8001 python -m src.main`
QUICKEOF

cat > PROJECT_SUMMARY.md << 'SUMMARYEOF'
# Project Summary - ETF Compliance Workflow Engine

## What This Demonstrates

✅ **Regulated workflow systems** - State machines, audit trails, immutability  
✅ **Backend architecture** - Type-safe APIs, service separation  
✅ **Observability** - Complete audit logging  
✅ **AI integration** - Augments human judgment  
✅ **Production mindset** - Tests, docs, scalability

## Interview Talking Points

### "Walk me through your demo"

> "I built a compliance workflow engine that enforces SEC filing requirements in code. It uses a state machine to prevent invalid shortcuts, logs every action to an immutable audit trail, and adds AI validation that catches quality issues while keeping humans in the loop."

### "Why these architecture choices?"

> "The state machine enforces legal requirements - approved filings are immutable like real SEC submissions. The audit log is append-only for compliance audits. Two-layer validation shows how LLMs augment workflows without replacing judgment."

### "How would you scale this?"

> "PostgreSQL with replication, auth and RBAC, retry logic for AI, structured logging, monitoring. The service separation makes horizontal scaling easy. Add webhooks, configurable approvals, and AI feedback loops."

## Key Files

- **src/services/workflow.py** - State machine logic
- **src/services/audit.py** - Immutable audit trail
- **src/services/validation.py** - Two-layer validation
- **src/routes/filings.py** - Complete workflow API

## Tech Stack

- FastAPI (type-safe, auto docs)
- SQLite (ACID, simple - would use Postgres in prod)
- Pydantic (runtime validation)
- Claude API (AI validation)
SUMMARYEOF

echo "  ✅ README.md"
echo "  ✅ QUICKSTART.md"
echo "  ✅ PROJECT_SUMMARY.md"
echo ""

# ============================================================================
# 3. CREATE CONFIG FILES
# ============================================================================

echo "⚙️  Creating config files..."

cat > .env.example << 'ENVEOF'
# ETF Compliance Workflow Engine - Environment Configuration

# Anthropic API (for AI-powered validation)
# Get your API key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
ENVEOF

cat > .gitignore << 'GITEOF'
# Python
__pycache__/
*.py[cod]
*.pyc
.Python
*.egg-info/
dist/
build/

# Virtual Environments
venv/
env/
.venv

# Environment
.env

# Database
*.db
*.sqlite
database/etf_compliance.db

# Testing
.pytest_cache/
.coverage

# IDEs
.vscode/
.idea/
.DS_Store
GITEOF

echo "  ✅ .env.example"
echo "  ✅ .gitignore"
echo ""

# ============================================================================
# DONE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Your CorgiDemo folder now has:"
echo ""
echo "📦 Python packages:"
echo "  ✅ src/__init__.py"
echo "  ✅ src/routes/__init__.py"
echo "  ✅ src/services/__init__.py"
echo "  ✅ src/utils/__init__.py"
echo "  ✅ tests/__init__.py"
echo ""
echo "📄 Documentation:"
echo "  ✅ README.md - Full architecture docs"
echo "  ✅ QUICKSTART.md - 5-minute setup guide"
echo "  ✅ PROJECT_SUMMARY.md - Interview prep"
echo ""
echo "⚙️  Configuration:"
echo "  ✅ .env.example - Config template"
echo "  ✅ .gitignore - Git ignore rules"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Ready to run!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo ""
echo "  1. pip install -r requirements.txt"
echo "  2. python -m src.database"
echo "  3. python -m src.main"
echo ""
echo "Then visit: http://localhost:8000/docs"
echo ""