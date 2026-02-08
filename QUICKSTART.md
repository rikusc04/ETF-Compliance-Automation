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
