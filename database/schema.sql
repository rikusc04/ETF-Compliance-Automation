-- ETF Compliance Workflow Engine - Database Schema
-- Designed for auditability and traceability

-- Core filings table
CREATE TABLE IF NOT EXISTS filings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_name TEXT NOT NULL,
    filing_type TEXT NOT NULL,  -- 'N-PORT', 'N-CEN', '485BPOS', etc.
    version INTEGER DEFAULT 1,
    status TEXT NOT NULL,        -- 'draft', 'pending_review', 'approved', 'rejected'
    content TEXT NOT NULL,       -- Filing data as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT NOT NULL,
    parent_filing_id INTEGER,    -- For versioning chain
    FOREIGN KEY (parent_filing_id) REFERENCES filings(id)
);

-- Immutable audit trail
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_id INTEGER NOT NULL,
    action TEXT NOT NULL,        -- 'created', 'submitted', 'approved', 'rejected', 'revised'
    actor TEXT NOT NULL,          -- User/system identifier
    previous_status TEXT,
    new_status TEXT,
    metadata TEXT,               -- Additional context as JSON
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (filing_id) REFERENCES filings(id)
);

-- Approval requirements per filing type
CREATE TABLE IF NOT EXISTS approval_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_type TEXT NOT NULL UNIQUE,
    required_approvers TEXT NOT NULL,  -- JSON array: ['compliance_officer', 'legal', 'cco']
    validation_rules TEXT              -- JSON: field requirements
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_filings_status ON filings(status);
CREATE INDEX IF NOT EXISTS idx_filings_type ON filings(filing_type);
CREATE INDEX IF NOT EXISTS idx_audit_filing ON audit_log(filing_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor);