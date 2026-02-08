"""
Audit Service - Immutable logging for compliance workflows.
Every action on a filing MUST be logged.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from ..database import get_db


class AuditService:
    """
    Manages audit trail for all filing operations.
    
    Design principles:
    - Immutable: audit entries are never updated or deleted
    - Complete: every state change is logged
    - Traceable: who, what, when, why
    """
    
    def record(
        self,
        filing_id: int,
        action: str,
        actor: str,
        previous_status: Optional[str] = None,
        new_status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Record an audit entry.
        
        Args:
            filing_id: ID of the filing
            action: Action performed (e.g., 'created', 'submitted', 'approved')
            actor: Who performed the action
            previous_status: Status before action
            new_status: Status after action
            metadata: Additional context (comments, validation results, etc.)
            
        Returns:
            ID of the audit log entry
        """
        with get_db() as conn:
            cursor = conn.execute(
                """
                INSERT INTO audit_log (filing_id, action, actor, previous_status, new_status, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    filing_id,
                    action,
                    actor,
                    previous_status,
                    new_status,
                    json.dumps(metadata) if metadata else None
                )
            )
            return cursor.lastrowid
    
    def get_filing_history(self, filing_id: int) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for a filing.
        
        Returns entries in reverse chronological order (newest first).
        """
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM audit_log 
                WHERE filing_id = ? 
                ORDER BY timestamp DESC
                """,
                (filing_id,)
            )
            return cursor.fetchall()
    
    def get_actor_history(self, actor: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all actions by a specific actor."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT al.*, f.filing_name, f.filing_type
                FROM audit_log al
                JOIN filings f ON al.filing_id = f.id
                WHERE al.actor = ?
                ORDER BY al.timestamp DESC
                LIMIT ?
                """,
                (actor, limit)
            )
            return cursor.fetchall()
    
    def get_recent_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity across all filings."""
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT al.*, f.filing_name, f.filing_type
                FROM audit_log al
                JOIN filings f ON al.filing_id = f.id
                ORDER BY al.timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            return cursor.fetchall()
    
    def get_status_changes(self, filing_id: int) -> List[Dict[str, Any]]:
        """
        Get only status change events for a filing.
        Useful for tracking approval workflow.
        """
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM audit_log
                WHERE filing_id = ? 
                  AND new_status IS NOT NULL
                ORDER BY timestamp ASC
                """,
                (filing_id,)
            )
            return cursor.fetchall()
    
    def verify_chain_of_custody(self, filing_id: int) -> Dict[str, Any]:
        """
        Verify complete chain of custody for a filing.
        
        Returns:
            Summary including:
            - Total actions
            - Unique actors
            - Status transitions
            - Time to approval (if approved)
        """
        history = self.get_filing_history(filing_id)
        
        if not history:
            return {"valid": False, "reason": "No audit trail found"}
        
        actors = set(entry['actor'] for entry in history)
        status_changes = [
            entry for entry in history 
            if entry.get('new_status')
        ]
        
        result = {
            "valid": True,
            "total_actions": len(history),
            "unique_actors": list(actors),
            "status_transitions": len(status_changes),
            "created_at": history[-1]['timestamp'] if history else None,
            "current_status": history[0].get('new_status') if history else None
        }
        
        # Calculate time to approval if applicable
        approved_entry = next(
            (e for e in history if e.get('new_status') == 'approved'),
            None
        )
        if approved_entry and history:
            created = datetime.fromisoformat(history[-1]['timestamp'])
            approved = datetime.fromisoformat(approved_entry['timestamp'])
            result['time_to_approval_seconds'] = (approved - created).total_seconds()
        
        return result
