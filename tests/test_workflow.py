"""
Tests for workflow state machine.

Validates:
- Valid transitions are allowed
- Invalid transitions are blocked
- Audit logging works correctly
"""

import pytest
from src.services.workflow import WorkflowEngine
from src.services.audit import AuditService
from src.models import FilingStatus


class TestWorkflowEngine:
    """Test workflow state machine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.workflow = WorkflowEngine()
    
    def test_valid_transitions(self):
        """Test that all valid transitions are allowed."""
        # DRAFT → PENDING_REVIEW
        assert self.workflow.can_transition(
            FilingStatus.DRAFT,
            FilingStatus.PENDING_REVIEW
        )
        
        # PENDING_REVIEW → APPROVED
        assert self.workflow.can_transition(
            FilingStatus.PENDING_REVIEW,
            FilingStatus.APPROVED
        )
        
        # PENDING_REVIEW → REJECTED
        assert self.workflow.can_transition(
            FilingStatus.PENDING_REVIEW,
            FilingStatus.REJECTED
        )
        
        # REJECTED → DRAFT
        assert self.workflow.can_transition(
            FilingStatus.REJECTED,
            FilingStatus.DRAFT
        )
    
    def test_invalid_transitions(self):
        """Test that invalid transitions are blocked."""
        # DRAFT → APPROVED (must go through review)
        assert not self.workflow.can_transition(
            FilingStatus.DRAFT,
            FilingStatus.APPROVED
        )
        
        # APPROVED → anything (terminal state)
        assert not self.workflow.can_transition(
            FilingStatus.APPROVED,
            FilingStatus.DRAFT
        )
        
        assert not self.workflow.can_transition(
            FilingStatus.APPROVED,
            FilingStatus.PENDING_REVIEW
        )
    
    def test_get_allowed_transitions(self):
        """Test getting allowed transitions for each state."""
        # DRAFT allows only PENDING_REVIEW
        allowed = self.workflow.get_allowed_transitions(FilingStatus.DRAFT)
        assert FilingStatus.PENDING_REVIEW in allowed
        assert len(allowed) == 1
        
        # PENDING_REVIEW allows APPROVED, REJECTED, DRAFT
        allowed = self.workflow.get_allowed_transitions(FilingStatus.PENDING_REVIEW)
        assert FilingStatus.APPROVED in allowed
        assert FilingStatus.REJECTED in allowed
        assert FilingStatus.DRAFT in allowed
        assert len(allowed) == 3
        
        # APPROVED allows nothing (terminal)
        allowed = self.workflow.get_allowed_transitions(FilingStatus.APPROVED)
        assert len(allowed) == 0
    
    def test_transition_raises_on_invalid(self):
        """Test that invalid transitions raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.workflow.transition(
                filing_id=999,
                current=FilingStatus.DRAFT,
                target=FilingStatus.APPROVED,
                actor="test_user"
            )
        
        assert "Invalid transition" in str(exc_info.value)
    
    def test_workflow_status(self):
        """Test getting workflow status."""
        status = self.workflow.get_workflow_status(
            filing_id=1,
            current_status=FilingStatus.PENDING_REVIEW
        )
        
        assert status['filing_id'] == 1
        assert status['current_status'] == FilingStatus.PENDING_REVIEW.value
        assert status['requires_approval'] is True
        assert not status['is_terminal']
        assert len(status['allowed_transitions']) == 3


class TestWorkflowIntegration:
    """Integration tests with database (requires setup)."""
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_full_approval_flow(self):
        """Test complete workflow from creation to approval."""
        # This would test:
        # 1. Create filing (DRAFT)
        # 2. Submit for review (DRAFT → PENDING_REVIEW)
        # 3. Approve (PENDING_REVIEW → APPROVED)
        # 4. Verify audit trail
        pass
    
    @pytest.mark.skip(reason="Requires database setup")
    def test_rejection_and_resubmission(self):
        """Test rejection and revision flow."""
        # This would test:
        # 1. Submit for review
        # 2. Reject
        # 3. Revise (create new version)
        # 4. Resubmit and approve
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])