"""
Audit log API routes.

Endpoints for querying audit trails and compliance reporting.
"""

from fastapi import APIRouter, Query
from typing import List, Optional

from ..models import AuditLogEntry
from ..services.audit import AuditService


router = APIRouter(prefix="/audit", tags=["audit"])
audit_service = AuditService()


@router.get("/recent", response_model=List[AuditLogEntry])
async def get_recent_activity(limit: int = Query(50, le=200)):
    """
    Get recent activity across all filings.
    
    Useful for compliance dashboards and monitoring.
    """
    activity = audit_service.get_recent_activity(limit)
    return [AuditLogEntry(**entry) for entry in activity]


@router.get("/actor/{actor}", response_model=List[AuditLogEntry])
async def get_actor_history(actor: str, limit: int = Query(100, le=500)):
    """
    Get all actions by a specific actor.
    
    Useful for:
    - User activity reports
    - Compliance audits
    - Access reviews
    """
    history = audit_service.get_actor_history(actor, limit)
    return [AuditLogEntry(**entry) for entry in history]


@router.get("/filing/{filing_id}/custody")
async def verify_chain_of_custody(filing_id: int):
    """
    Verify complete chain of custody for a filing.
    
    Returns comprehensive audit summary:
    - Total actions
    - Unique actors
    - Status transitions
    - Time to approval
    """
    return audit_service.verify_chain_of_custody(filing_id)


@router.get("/filing/{filing_id}/status-changes", response_model=List[AuditLogEntry])
async def get_status_changes(filing_id: int):
    """
    Get only status change events for a filing.
    
    Filters audit log to show workflow transitions.
    """
    changes = audit_service.get_status_changes(filing_id)
    return [AuditLogEntry(**entry) for entry in changes]