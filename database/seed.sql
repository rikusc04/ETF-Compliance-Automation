-- Seed data for development and testing

-- Insert approval requirements for different filing types
INSERT OR IGNORE INTO approval_requirements (filing_type, required_approvers, validation_rules) VALUES
(
    'N-PORT',
    '["compliance_officer", "fund_accountant"]',
    '{"required_fields": ["fund_name", "reporting_period_end", "total_assets", "holdings", "series_id"], "max_holdings": 10000}'
),
(
    'N-CEN',
    '["compliance_officer", "legal", "cco"]',
    '{"required_fields": ["fund_name", "fiscal_year_end", "total_net_assets"], "annual_only": true}'
),
(
    '485BPOS',
    '["legal", "cco", "board_representative"]',
    '{"required_fields": ["prospectus_text", "effective_date", "fund_name"], "requires_board_approval": true}'
);

-- Sample filing for testing
INSERT OR IGNORE INTO filings (filing_name, filing_type, status, content, created_by, created_at) VALUES
(
    'Q4 2024 Holdings Report',
    'N-PORT',
    'draft',
    '{"fund_name": "Corgi Growth ETF", "series_id": "S000012345", "reporting_period_end": "2024-12-31", "total_assets": 150000000, "holdings": [{"ticker": "AAPL", "shares": 10000, "value": 1850000}]}',
    'system_seed',
    datetime('now', '-2 days')
);