# ETF Compliance Workflow Engine

A lightweight system for managing regulatory filing workflows with built-in auditability and AI-assisted validation.

## Purpose

This project is an ETF Compliance Workflow Engine built to simulate regulatory filings. The goal was to design a validation workflow that enforces rules through the system itself.

This system demonstrates how to turn manual ETF compliance workflows into structured, auditable software. It shows:

1. **State machine enforcement** for regulatory approval flows
2. **Immutable audit trails** for SEC compliance
3. **AI-assisted validation** that augments (not replaces) human judgment
4. **Version control** for filing lineage

---

## Architecture Decisions

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

## Setup & Usage

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
1. Configure Python environment:
```bash
python3 -m venv venv
```

2. Activate Python environemnt:
```bash
source venv/bin/activate
```

3. Install all requirements:
```bash
pip install -r requirements.txt
```

4. Initialize the Database
```bash
python -m src.database
```

5. Start the Server
```bash
python -m src.main
```
- Optionally, if you want to reset the database every time you start the server, run the command:
```bash
RESET_DB=true python -m src.main
```
- Server runs at: http://localhost:8000
- Interactive API documentation: http://localhost:8000/docs
- On first startup, the database is automatically initialized and populated with example seed data
---

## API Examples

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

## Production Considerations

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

## Project Structure

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

## Tech Stack

- FastAPI (type-safe, auto docs)
- SQLite (ACID, simple - would use Postgres in prod)
- Pydantic (runtime validation)
- Claude API (AI validation)

--

## Key Takeaways

This architecture demonstrates:

1. **Regulated Workflow Thinking** - State machines enforce compliance, every action is traceable
2. **Backend Architecture** - Type-safe API, separation of concerns, proper error handling
3. **Observability** - Complete audit trail, chain of custody verification
4. **AI Integration** - Thoughtful LLM use (augment, not replace), graceful degradation

Real-world applications: ETF/fund compliance, financial reporting, document management, change control systems.