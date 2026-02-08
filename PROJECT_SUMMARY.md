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
