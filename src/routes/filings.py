"""
Filing management API routes.

Endpoints:
- POST /filings - Create new filing
- GET /filings/{id} - Get filing details
- POST /filings/{id}/submit - Submit for review
- POST /filings/{id}/approve - Approve/reject filing
- POST /filings/{id}/revise - Create new version
- GET /filings/{id}/history - Get audit trail
- GET /filings - List filings
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import json

from ..models import (
    FilingCreate, FilingResponse, ApprovalRequest, 
    SubmitRequest, AuditLogEntry, FilingStatus,
    WorkflowStatus, VersionHistory, FilingUpdate
)
from ..database import get_db, get_filing_by_id, insert_filing, update_filing_status
from ..services.workflow import WorkflowEngine
from ..services.validation import LLMValidator
from ..services.audit import AuditService


router = APIRouter(prefix="/filings", tags=["filings"])

# Initialize services
workflow_engine = WorkflowEngine()
validator = LLMValidator(use_ai=True)
audit_service = AuditService()


@router.post("/", response_model=FilingResponse, status_code=201)
async def create_filing(filing: FilingCreate):
    """
    Create a new filing with validation.
    
    Steps:
    1. Validate required fields and content
    2. Insert into database
    3. Log creation to audit trail
    """
    # Validate structure
    validation = validator.validate_structure(filing.filing_type, filing.content)
    
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Filing validation failed",
                "missing_fields": validation.missing_fields,
                "required_fields": validator.REQUIRED_FIELDS.get(filing.filing_type, [])
            }
        )
    
    # Insert filing
    filing_id = insert_filing({
        'filing_name': filing.filing_name,
        'filing_type': filing.filing_type.value,
        'status': FilingStatus.DRAFT.value,
        'content': filing.content,
        'created_by': filing.created_by,
        'version': 1
    })
    
    # Log creation
    audit_service.record(
        filing_id=filing_id,
        action="created",
        actor=filing.created_by,
        new_status=FilingStatus.DRAFT.value,
        metadata={
            "warnings": validation.warnings,
            "ai_suggestion": validation.ai_suggestion
        }
    )
    
    # Return created filing
    filing_data = get_filing_by_id(filing_id)
    return FilingResponse(**filing_data)


@router.get("/{filing_id}", response_model=FilingResponse)
async def get_filing(filing_id: int):
    """Get filing by ID."""
    try:
        filing_data = get_filing_by_id(filing_id)
        return FilingResponse(**filing_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[FilingResponse])
async def list_filings(
    status: Optional[FilingStatus] = None,
    filing_type: Optional[str] = None,
    limit: int = Query(50, le=200)
):
    """
    List filings with optional filters.
    
    Query params:
    - status: Filter by status
    - filing_type: Filter by type
    - limit: Max results (default 50, max 200)
    """
    with get_db() as conn:
        query = "SELECT * FROM filings WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status.value)
        
        if filing_type:
            query += " AND filing_type = ?"
            params.append(filing_type)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        results = cursor.fetchall()
        
        return [FilingResponse(**row) for row in results]


@router.post("/{filing_id}/submit", response_model=dict)
async def submit_for_review(filing_id: int, request: SubmitRequest):
    """
    Submit filing for review (DRAFT → PENDING_REVIEW).
    
    Validates:
    - Filing exists
    - Current status allows submission
    - Filing passes validation
    """
    # Get filing
    try:
        filing = get_filing_by_id(filing_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    current_status = FilingStatus(filing['status'])
    
    # Validate transition is allowed
    if not workflow_engine.can_transition(current_status, FilingStatus.PENDING_REVIEW):
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Cannot submit filing in {current_status.value} status",
                "allowed_transitions": [
                    s.value for s in workflow_engine.get_allowed_transitions(current_status)
                ]
            }
        )
    
    # Re-validate filing before submission
    validation = validator.validate_structure(
        filing['filing_type'],
        filing['content']
    )
    
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Filing validation failed",
                "missing_fields": validation.missing_fields
            }
        )
    
    # Execute transition
    workflow_engine.transition(
        filing_id=filing_id,
        current=current_status,
        target=FilingStatus.PENDING_REVIEW,
        actor=request.actor,
        metadata={"validation_warnings": validation.warnings}
    )
    
    # Update database
    update_filing_status(filing_id, FilingStatus.PENDING_REVIEW.value)
    
    return {
        "status": "submitted",
        "filing_id": filing_id,
        "new_status": FilingStatus.PENDING_REVIEW.value,
        "warnings": validation.warnings
    }


@router.post("/{filing_id}/approve", response_model=dict)
async def approve_filing(filing_id: int, approval: ApprovalRequest):
    """
    Approve or reject a filing.
    
    PENDING_REVIEW → APPROVED (if approved=True)
    PENDING_REVIEW → REJECTED (if approved=False)
    """
    # Get filing
    try:
        filing = get_filing_by_id(filing_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    current_status = FilingStatus(filing['status'])
    target_status = FilingStatus.APPROVED if approval.approved else FilingStatus.REJECTED
    
    # Validate transition
    if not workflow_engine.can_transition(current_status, target_status):
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Cannot transition from {current_status.value} to {target_status.value}",
                "allowed_transitions": [
                    s.value for s in workflow_engine.get_allowed_transitions(current_status)
                ]
            }
        )
    
    # Execute transition
    workflow_engine.transition(
        filing_id=filing_id,
        current=current_status,
        target=target_status,
        actor=approval.reviewer,
        metadata={
            "comments": approval.comments,
            "approved": approval.approved
        }
    )
    
    # Update database
    update_filing_status(filing_id, target_status.value)
    
    return {
        "status": "approved" if approval.approved else "rejected",
        "filing_id": filing_id,
        "new_status": target_status.value,
        "reviewer": approval.reviewer
    }


@router.post("/{filing_id}/revise", response_model=FilingResponse)
async def create_revision(filing_id: int, update: FilingUpdate):
    """
    Create a new version of a filing.
    
    Creates a new filing record that:
    - References parent via parent_filing_id
    - Increments version number
    - Starts in DRAFT status
    """
    # Get parent filing
    try:
        parent = get_filing_by_id(filing_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Validate content
    validation = validator.validate_structure(
        parent['filing_type'],
        update.content
    )
    
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Filing validation failed",
                "missing_fields": validation.missing_fields
            }
        )
    
    # Create new version
    new_version = parent['version'] + 1
    new_filing_id = insert_filing({
        'filing_name': parent['filing_name'],
        'filing_type': parent['filing_type'],
        'status': FilingStatus.DRAFT.value,
        'content': update.content,
        'created_by': update.updated_by,
        'version': new_version,
        'parent_filing_id': filing_id
    })
    
    # Log revision
    audit_service.record(
        filing_id=new_filing_id,
        action="revised",
        actor=update.updated_by,
        new_status=FilingStatus.DRAFT.value,
        metadata={
            "parent_filing_id": filing_id,
            "version": new_version
        }
    )
    
    new_filing = get_filing_by_id(new_filing_id)
    return FilingResponse(**new_filing)


@router.get("/{filing_id}/history", response_model=List[AuditLogEntry])
async def get_filing_history(filing_id: int):
    """
    Get complete audit trail for a filing.
    
    Returns all actions in reverse chronological order.
    """
    # Verify filing exists
    try:
        get_filing_by_id(filing_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    history = audit_service.get_filing_history(filing_id)
    return [AuditLogEntry(**entry) for entry in history]


@router.get("/{filing_id}/workflow", response_model=WorkflowStatus)
async def get_workflow_status(filing_id: int):
    """
    Get current workflow status and allowed actions.
    
    Returns:
    - Current status
    - Allowed next transitions
    - Whether approval is required
    """
    try:
        filing = get_filing_by_id(filing_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    current_status = FilingStatus(filing['status'])
    status = workflow_engine.get_workflow_status(filing_id, current_status)
    
    return WorkflowStatus(
        filing_id=status['filing_id'],
        current_status=current_status,
        allowed_transitions=[FilingStatus(s) for s in status['allowed_transitions']],
        requires_approval=status['requires_approval'],
        approval_count=status['approval_count']
    )


@router.get("/{filing_id}/versions", response_model=List[VersionHistory])
async def get_filing_versions(filing_id: int):
    """
    Get version history for a filing.
    
    Returns all versions in the filing's lineage.
    """
    # Verify filing exists
    try:
        filing = get_filing_by_id(filing_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    with get_db() as conn:
        # Get all versions in this filing's chain
        cursor = conn.execute(
            """
            WITH RECURSIVE filing_chain AS (
                -- Start with the requested filing
                SELECT id, filing_name, version, parent_filing_id, created_at, created_by, status
                FROM filings
                WHERE id = ?
                
                UNION ALL
                
                -- Get parent filings
                SELECT f.id, f.filing_name, f.version, f.parent_filing_id, f.created_at, f.created_by, f.status
                FROM filings f
                INNER JOIN filing_chain fc ON f.id = fc.parent_filing_id
            )
            SELECT * FROM filing_chain
            ORDER BY version ASC
            """,
            (filing_id,)
        )
        
        versions = cursor.fetchall()
        
        return [
            VersionHistory(
                filing_id=v['id'],
                version=v['version'],
                parent_filing_id=v['parent_filing_id'],
                created_at=v['created_at'],
                created_by=v['created_by'],
                status=FilingStatus(v['status'])
            )
            for v in versions
        ]