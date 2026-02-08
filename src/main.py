"""
ETF Compliance Workflow Engine - Main Application

FastAPI application for managing regulatory filing workflows.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routes import filings_router, audit_router
from .utils.config import config
from .database import init_database


# Initialize database on startup
try:
    init_database(reset=False)
except Exception as e:
    print(f"⚠️  Database initialization skipped: {e}")


# Create FastAPI app
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description=config.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(filings_router)
app.include_router(audit_router)


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


def main():
    """Run the application."""
    config.validate()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║  ETF Compliance Workflow Engine                               ║
║  Version {config.API_VERSION}                                            ║
╚═══════════════════════════════════════════════════════════════╝

🚀 Starting server...
📍 URL: http://{config.HOST}:{config.PORT}
📚 Docs: http://{config.HOST}:{config.PORT}/docs
🔍 Health: http://{config.HOST}:{config.PORT}/health

Features:
✅ State machine workflow enforcement
✅ Immutable audit trail
{"✅ AI-powered validation (Claude)" if config.ANTHROPIC_API_KEY else "⚠️  AI validation disabled (no API key)"}
✅ Filing version control

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