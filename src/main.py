"""
ETF Compliance Workflow Engine - Main Application

FastAPI application for managing regulatory filing workflows.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from contextlib import asynccontextmanager

from .routes import filings_router, audit_router
from .utils.config import config
from .database import init_database


# --------------------------------------------------
# Lifespan (startup/shutdown lifecycle)
# --------------------------------------------------

RESET_DB = os.getenv("RESET_DB") == "true"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once when the app starts and once when it shuts down.
    """

    # --- Startup ---
    try:
        init_database(reset=RESET_DB)
        print(f"Database initialized (reset={RESET_DB})")
    except Exception as e:
        print(f"Database initialization skipped: {e}")

    yield

    # --- Shutdown (optional cleanup here) ---


# --------------------------------------------------
# Create FastAPI app
# --------------------------------------------------

app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# --------------------------------------------------
# Middleware
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(filings_router)
app.include_router(audit_router)


# --------------------------------------------------
# Routes
# --------------------------------------------------

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": config.API_TITLE,
        "version": config.API_VERSION,
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "filings": "/filings",
            "audit": "/audit"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "ai_validation": "enabled" if config.ANTHROPIC_API_KEY else "disabled"
    }


# --------------------------------------------------
# Entry point
# --------------------------------------------------

def main():
    """Run the application."""
    config.validate()

    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║  ETF Compliance Workflow Engine                               ║
║  Version {config.API_VERSION}                                 ║
╚═══════════════════════════════════════════════════════════════╝

Starting server...
URL: http://{config.HOST}:{config.PORT}
Docs: http://{config.HOST}:{config.PORT}/docs
Health: http://{config.HOST}:{config.PORT}/health

Features:
State machine workflow enforcement
Immutable audit trail
{"AI-powered validation (Claude)" if config.ANTHROPIC_API_KEY else "AI validation disabled (no API key)"}
Filing version control

Press Ctrl+C to stop
""")

    uvicorn.run(
        "src.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )


if __name__ == "__main__":
    main()