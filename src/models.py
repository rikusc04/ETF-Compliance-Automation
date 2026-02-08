"""
Pydantic models for ETF Compliance Workflow Engine.
Provides type safety, validation, and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class FilingStatus(str, Enum):
    """Valid filing statuses - enforces state machine."""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class FilingType(str, Enum):
    """SEC filing types for ETFs."""
    N_PORT = "N-PORT"
    N_CEN = "N-CEN"
    FORM_485BPOS = "485BPOS"
    FORM_497 = "497"
    FORM_NSAR = "N-SAR"


class FilingCreate(BaseModel):
    """Request model for creating a new filing."""
    filing_name: str = Field(..., min_length=1, max_length=255)
    filing_type: FilingType
    content: Dict[str, Any] = Field(..., description="Filing content as structured JSON")
    created_by: str = Field(..., min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "filing_name": "Q1 2025 Holdings Report",
                "filing_type": "N-PORT",
                "content": {
                    "fund_name": "Corgi Innovation ETF",
                    "series_id": "S000067890",
                    "reporting_period_end": "2025-03-31",
                    "total_assets": 250000000,
                    "holdings": [
                        {"ticker": "NVDA", "shares": 5000, "value": 4250000}
                    ]
                },
                "created_by": "john.doe@corgi.com"
            }
        }


class FilingResponse(BaseModel):
    """Response model for filing data."""
    id: int
    filing_name: str
    filing_type: str
    version: int
    status: FilingStatus
    content: Dict[str, Any]
    created_at: datetime
    created_by: str
    parent_filing_id: Optional[int] = None

    class Config:
        from_attributes = True


class FilingUpdate(BaseModel):
    """Request model for updating filing content."""
    content: Dict[str, Any]
    updated_by: str


class ApprovalRequest(BaseModel):
    """Request model for approving/rejecting a filing."""
    approved: bool = Field(..., description="True to approve, False to reject")
    reviewer: str = Field(..., min_length=1)
    comments: Optional[str] = Field(None, max_length=2000)

    class Config:
        json_schema_extra = {
            "example": {
                "approved": True,
                "reviewer": "jane.smith@corgi.com",
                "comments": "All holdings reconciled. Approved for submission."
            }
        }


class SubmitRequest(BaseModel):
    """Request model for submitting a filing for review."""
    actor: str = Field(..., min_length=1)


class AuditLogEntry(BaseModel):
    """Audit log entry - immutable record of actions."""
    id: int
    filing_id: int
    action: str
    actor: str
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ValidationResult(BaseModel):
    """Result from filing validation (both rules-based and AI)."""
    is_valid: bool
    missing_fields: List[str] = []
    warnings: List[str] = []
    ai_suggestion: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": False,
                "missing_fields": ["series_id", "reporting_period_end"],
                "warnings": ["Total assets seem unusually low for this fund size"],
                "ai_suggestion": "Consider adding expense ratio disclosure"
            }
        }


class WorkflowStatus(BaseModel):
    """Current workflow status and allowed actions."""
    filing_id: int
    current_status: FilingStatus
    allowed_transitions: List[FilingStatus]
    requires_approval: bool
    approval_count: int = 0


class VersionHistory(BaseModel):
    """Filing version history."""
    filing_id: int
    version: int
    parent_filing_id: Optional[int]
    created_at: datetime
    created_by: str
    status: FilingStatus