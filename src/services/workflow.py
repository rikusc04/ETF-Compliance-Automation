"""
Workflow Engine - State machine for filing approvals.

Enforces valid state transitions and ensures all changes are audited.
Mirrors SEC compliance expectations for regulated workflows.
"""

from typing import Dict, Optional, List
from ..models import FilingStatus
from .audit import AuditService


class WorkflowEngine:
    """
    State machine for filing workflow.
    
    Valid transitions:
    - DRAFT → PENDING_REVIEW (submit for approval)
    - PENDING_REVIEW → APPROVED (approve)
    - PENDING_REVIEW → REJECTED (reject)
    - PENDING_REVIEW → DRAFT (send back for revisions)
    - REJECTED → DRAFT (revise and resubmit)
    - APPROVED → (terminal state, no transitions)
    
    Design rationale:
    - Approved filings are immutable (create new version instead)
    - Every transition requires explicit actor identification
    - All transitions are logged to audit trail
    """
    
    # Define valid state transitions
    VALID_TRANSITIONS: Dict[FilingStatus, List[FilingStatus]] = {
        FilingStatus.DRAFT: [FilingStatus.PENDING_REVIEW],
        FilingStatus.PENDING_REVIEW: [
            FilingStatus.APPROVED,
            FilingStatus.REJECTED,
            FilingStatus.DRAFT  # Send back for revisions
        ],
        FilingStatus.APPROVED: [],  # Terminal state - immutable
        FilingStatus.REJECTED: [FilingStatus.DRAFT]  # Allow resubmission
    }
    
    # Human-readable transition names for audit log
    TRANSITION_NAMES: Dict[str, str] = {
        'draft->pending_review': 'submitted_for_review',
        'pending_review->approved': 'approved',
        'pending_review->rejected': 'rejected',
        'pending_review->draft': 'returned_for_revision',
        'rejected->draft': 'revised'
    }
    
    def __init__(self, audit_service: Optional[AuditService] = None):
        self.audit = audit_service or AuditService()
    
    def can_transition(
        self, 
        current: FilingStatus, 
        target: FilingStatus
    ) -> bool:
        """
        Check if a state transition is valid.
        
        Args:
            current: Current filing status
            target: Desired target status
            
        Returns:
            True if transition is allowed, False otherwise
        """
        allowed = self.VALID_TRANSITIONS.get(current, [])
        return target in allowed
    
    def get_allowed_transitions(
        self, 
        current: FilingStatus
    ) -> List[FilingStatus]:
        """Get list of allowed transitions from current state."""
        return self.VALID_TRANSITIONS.get(current, [])
    
    def transition(
        self,
        filing_id: int,
        current: FilingStatus,
        target: FilingStatus,
        actor: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Execute a state transition with audit logging.
        
        Args:
            filing_id: ID of the filing
            current: Current status
            target: Target status
            actor: Who is performing the transition
            metadata: Additional context (comments, reasons, etc.)
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If transition is not allowed
        """
        # Validate transition
        if not self.can_transition(current, target):
            allowed = self.get_allowed_transitions(current)
            raise ValueError(
                f"Invalid transition: {current.value} → {target.value}. "
                f"Allowed transitions from {current.value}: "
                f"{[s.value for s in allowed]}"
            )
        
        # Determine action name
        transition_key = f"{current.value}->{target.value}"
        action = self.TRANSITION_NAMES.get(
            transition_key,
            f"transition_{target.value}"
        )
        
        # Log to audit trail
        self.audit.record(
            filing_id=filing_id,
            action=action,
            actor=actor,
            previous_status=current.value,
            new_status=target.value,
            metadata=metadata or {}
        )
        
        return True
    
    def validate_approval_flow(
        self,
        filing_id: int,
        required_approvers: Optional[List[str]] = None
    ) -> Dict:
        """
        Validate that a filing has followed proper approval flow.
        
        Checks:
        - Has filing been through required states?
        - Were approvals from authorized actors?
        - Is chain of custody complete?
        
        Args:
            filing_id: Filing to validate
            required_approvers: List of required approver roles (optional)
            
        Returns:
            Validation result with details
        """
        # Get audit history
        history = self.audit.get_filing_history(filing_id)
        
        if not history:
            return {
                "valid": False,
                "reason": "No audit trail found"
            }
        
        # Check for required state transitions
        status_changes = [
            e for e in history 
            if e.get('new_status')
        ]
        
        states_visited = set(
            e['new_status'] for e in status_changes
        )
        
        # For approved filings, must have gone through PENDING_REVIEW
        current_status = status_changes[0].get('new_status') if status_changes else None
        
        if current_status == FilingStatus.APPROVED.value:
            if FilingStatus.PENDING_REVIEW.value not in states_visited:
                return {
                    "valid": False,
                    "reason": "Approved filing missing PENDING_REVIEW state"
                }
        
        result = {
            "valid": True,
            "states_visited": list(states_visited),
            "total_transitions": len(status_changes),
            "current_status": current_status
        }
        
        # If required approvers specified, validate
        if required_approvers:
            approval_events = [
                e for e in history
                if e.get('action') == 'approved'
            ]
            approvers = set(e['actor'] for e in approval_events)
            
            missing_approvers = set(required_approvers) - approvers
            if missing_approvers:
                result['valid'] = False
                result['missing_approvers'] = list(missing_approvers)
        
        return result
    
    def get_workflow_status(
        self,
        filing_id: int,
        current_status: FilingStatus
    ) -> Dict:
        """
        Get current workflow status and available actions.
        
        Returns:
            Dictionary with current state and allowed next steps
        """
        allowed = self.get_allowed_transitions(current_status)
        history = self.audit.get_filing_history(filing_id)
        
        # Count approvals
        approval_count = len([
            e for e in history
            if e.get('action') == 'approved'
        ])
        
        return {
            "filing_id": filing_id,
            "current_status": current_status.value,
            "allowed_transitions": [s.value for s in allowed],
            "is_terminal": len(allowed) == 0,
            "requires_approval": current_status == FilingStatus.PENDING_REVIEW,
            "approval_count": approval_count
        }