"""
Database connection and utilities.
Uses SQLite for simplicity - would use PostgreSQL in production.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
import json


DATABASE_PATH = Path(__file__).parent.parent / "database" / "etf_compliance.db"
SCHEMA_PATH = Path(__file__).parent.parent / "database" / "schema.sql"
SEED_PATH = Path(__file__).parent.parent / "database" / "seed.sql"


def dict_factory(cursor, row):
    """Convert SQLite row to dictionary."""
    d = {}
    for idx, col in enumerate(cursor.description):
        value = row[idx]
        # Parse JSON fields
        if col[0] in ['content', 'metadata', 'required_approvers', 'validation_rules']:
            try:
                d[col[0]] = json.loads(value) if value else None
            except (json.JSONDecodeError, TypeError):
                d[col[0]] = value
        else:
            d[col[0]] = value
    return d


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(
        DATABASE_PATH,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = dict_factory
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(reset: bool = False) -> None:
    """
    Initialize database with schema and seed data.
    
    Args:
        reset: If True, drop existing database and recreate
    """
    if reset and DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print("Deleted existing database")
    
    # Ensure database directory exists
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_connection()
    
    try:
        # Load and execute schema
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
        conn.executescript(schema)
        print("Database schema created")
        
        # Load and execute seed data
        with open(SEED_PATH, 'r') as f:
            seed = f.read()
        conn.executescript(seed)
        print("Seed data loaded")
        
        conn.commit()
        print(f"Database initialized at {DATABASE_PATH}")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()


def get_filing_by_id(filing_id: int) -> dict:
    """Helper to fetch filing by ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM filings WHERE id = ?",
            (filing_id,)
        )
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Filing {filing_id} not found")
        return result


def insert_filing(filing_data: dict) -> int:
    """Helper to insert filing and return ID."""
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO filings (filing_name, filing_type, status, content, created_by, version, parent_filing_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filing_data['filing_name'],
                filing_data['filing_type'],
                filing_data['status'],
                json.dumps(filing_data['content']),
                filing_data['created_by'],
                filing_data.get('version', 1),
                filing_data.get('parent_filing_id')
            )
        )
        return cursor.lastrowid


def update_filing_status(filing_id: int, new_status: str) -> None:
    """Helper to update filing status."""
    with get_db() as conn:
        conn.execute(
            "UPDATE filings SET status = ? WHERE id = ?",
            (new_status, filing_id)
        )


if __name__ == "__main__":
    # Initialize database when run directly
    init_database(reset=True)