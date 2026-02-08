"""
LLM-Assisted Validation Service.

Two-layer validation approach:
1. Hard rules: Required fields, data types, ranges
2. Soft validation: AI quality checks, consistency warnings

This shows how LLMs can augment compliance workflows without replacing human judgment.
"""

import os
import json
from typing import Dict, Any, List, Optional
from ..models import ValidationResult, FilingType


class LLMValidator:
    """
    Uses Claude to validate filing content quality.
    
    Design principle: AI assists, humans decide.
    - Hard rules (missing fields) → block submission
    - Soft warnings (quality issues) → flag for review
    """
    
    # Required fields per filing type (SEC mandated)
    REQUIRED_FIELDS: Dict[FilingType, List[str]] = {
        FilingType.N_PORT: [
            "fund_name",
            "series_id", 
            "reporting_period_end",
            "total_assets",
            "holdings"
        ],
        FilingType.N_CEN: [
            "fund_name",
            "fiscal_year_end",
            "total_net_assets",
            "series_id"
        ],
        FilingType.FORM_485BPOS: [
            "fund_name",
            "prospectus_text",
            "effective_date",
            "series_id"
        ]
    }
    
    # Value constraints (simple examples)
    VALIDATION_RULES: Dict[FilingType, Dict[str, Any]] = {
        FilingType.N_PORT: {
            "max_holdings": 10000,
            "min_total_assets": 0
        },
        FilingType.N_CEN: {
            "min_total_net_assets": 0
        }
    }
    
    def __init__(self, use_ai: bool = True):
        """
        Initialize validator.
        
        Args:
            use_ai: Whether to use Claude for quality checks (can disable for testing)
        """
        self.use_ai = use_ai and bool(os.getenv("ANTHROPIC_API_KEY"))
        
        if self.use_ai:
            try:
                import anthropic
                self.client = anthropic.Anthropic(
                    api_key=os.getenv("ANTHROPIC_API_KEY")
                )
            except ImportError:
                print("⚠️  anthropic package not installed. AI validation disabled.")
                self.use_ai = False
    
    def validate_structure(
        self,
        filing_type: FilingType,
        content: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate filing content with two-layer approach.
        
        Layer 1: Hard rules (required fields, constraints)
        Layer 2: AI quality check (if enabled)
        
        Args:
            filing_type: Type of SEC filing
            content: Filing content as JSON
            
        Returns:
            ValidationResult with errors and warnings
        """
        # Layer 1: Required fields check
        required = self.REQUIRED_FIELDS.get(filing_type, [])
        missing = [field for field in required if field not in content]
        
        # Check data type constraints
        warnings = self._check_constraints(filing_type, content)
        
        # Layer 2: AI quality check (only if no hard errors)
        ai_suggestion = None
        if not missing and self.use_ai:
            ai_result = self._llm_review(filing_type, content)
            if ai_result:
                warnings.extend(ai_result.get("warnings", []))
                ai_suggestion = ai_result.get("suggestion")
        
        return ValidationResult(
            is_valid=len(missing) == 0,
            missing_fields=missing,
            warnings=warnings,
            ai_suggestion=ai_suggestion
        )
    
    def _check_constraints(
        self,
        filing_type: FilingType,
        content: Dict[str, Any]
    ) -> List[str]:
        """Check value constraints and return warnings."""
        warnings = []
        rules = self.VALIDATION_RULES.get(filing_type, {})
        
        # N-PORT specific checks
        if filing_type == FilingType.N_PORT:
            # Check holdings count
            holdings = content.get("holdings", [])
            max_holdings = rules.get("max_holdings", 10000)
            if len(holdings) > max_holdings:
                warnings.append(
                    f"Holdings count ({len(holdings)}) exceeds maximum ({max_holdings})"
                )
            
            # Check total assets
            total_assets = content.get("total_assets", 0)
            if total_assets <= 0:
                warnings.append("Total assets must be greater than zero")
            
            # Check holdings sum vs total assets (tolerance check)
            if holdings:
                holdings_sum = sum(h.get("value", 0) for h in holdings)
                if abs(holdings_sum - total_assets) / total_assets > 0.05:  # 5% tolerance
                    warnings.append(
                        f"Holdings sum (${holdings_sum:,.0f}) differs from "
                        f"total assets (${total_assets:,.0f}) by >5%"
                    )
        
        return warnings
    
    def _llm_review(
        self,
        filing_type: FilingType,
        content: Dict[str, Any]
    ) -> Optional[Dict]:
        """
        Ask Claude to review filing quality.
        
        Returns:
            Dictionary with warnings and suggestions, or None if error
        """
        if not self.use_ai:
            return None
        
        # Build prompt
        prompt = f"""You are reviewing a {filing_type.value} filing for an ETF issuer.

Filing Content:
{json.dumps(content, indent=2)}

Perform a quality check:

1. Are numeric values reasonable? (e.g., total assets, holdings values)
2. Is the reporting period valid and recent?
3. For holdings data: do ticker symbols look valid? Are values reasonable?
4. Any obvious inconsistencies or missing context?

Respond ONLY with valid JSON in this exact format (no markdown, no backticks):
{{
  "warnings": ["warning 1", "warning 2"],
  "suggestion": "optional improvement suggestion"
}}

If everything looks good, return empty arrays:
{{
  "warnings": [],
  "suggestion": null
}}"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract text content
            response_text = message.content[0].text.strip()
            
            # Parse JSON (remove any markdown if present)
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(response_text)
            
            return result
            
        except Exception as e:
            # Don't fail validation if AI check fails
            print(f"⚠️  AI validation failed: {e}")
            return {"warnings": [], "suggestion": None}
    
    def validate_against_rules(
        self,
        filing_type: FilingType,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get detailed validation report.
        
        Returns full validation details including:
        - Required fields status
        - Constraint violations
        - AI feedback
        """
        validation = self.validate_structure(filing_type, content)
        
        return {
            "is_valid": validation.is_valid,
            "missing_fields": validation.missing_fields,
            "warnings": validation.warnings,
            "ai_suggestion": validation.ai_suggestion,
            "required_fields": self.REQUIRED_FIELDS.get(filing_type, []),
            "fields_present": [
                field for field in self.REQUIRED_FIELDS.get(filing_type, [])
                if field in content
            ]
        }