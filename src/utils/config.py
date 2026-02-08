"""
Application configuration.
"""

import os
from typing import Optional


class Config:
    """Application configuration from environment variables."""
    
    # API Configuration
    API_TITLE = "ETF Compliance Workflow Engine"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = """
    A lightweight system for managing regulatory filing workflows with built-in 
    auditability and AI-assisted validation.
    
    Features:
    - State machine enforcement for filing approvals
    - Immutable audit trail
    - AI-powered validation
    - Version control for filings
    """
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Anthropic API
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    
    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "database/etf_compliance.db")
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration and warn about missing optional settings."""
        if not cls.ANTHROPIC_API_KEY:
            print("⚠️  ANTHROPIC_API_KEY not set. AI validation will be disabled.")
            print("   Set it in .env file or environment variables to enable AI features.")


config = Config()