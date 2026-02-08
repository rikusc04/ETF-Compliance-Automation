"""
Tests for filing validation service.

Tests both hard rules (required fields) and AI validation logic.
"""

import pytest
from src.services.validation import LLMValidator
from src.models import FilingType


class TestLLMValidator:
    """Test filing validation logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Disable AI for unit tests
        self.validator = LLMValidator(use_ai=False)
    
    def test_valid_nport_filing(self):
        """Test validation of a valid N-PORT filing."""
        content = {
            "fund_name": "Test ETF",
            "series_id": "S000012345",
            "reporting_period_end": "2025-03-31",
            "total_assets": 100000000,
            "holdings": [
                {"ticker": "AAPL", "shares": 1000, "value": 185000}
            ]
        }
        
        result = self.validator.validate_structure(FilingType.N_PORT, content)
        
        assert result.is_valid is True
        assert len(result.missing_fields) == 0
    
    def test_missing_required_fields(self):
        """Test that missing required fields are detected."""
        content = {
            "fund_name": "Test ETF",
            # Missing: series_id, reporting_period_end, total_assets, holdings
        }
        
        result = self.validator.validate_structure(FilingType.N_PORT, content)
        
        assert result.is_valid is False
        assert "series_id" in result.missing_fields
        assert "reporting_period_end" in result.missing_fields
        assert "total_assets" in result.missing_fields
        assert "holdings" in result.missing_fields
    
    def test_zero_total_assets_warning(self):
        """Test that zero total assets generates warning."""
        content = {
            "fund_name": "Test ETF",
            "series_id": "S000012345",
            "reporting_period_end": "2025-03-31",
            "total_assets": 0,  # Invalid
            "holdings": []
        }
        
        result = self.validator.validate_structure(FilingType.N_PORT, content)
        
        assert result.is_valid is True  # Not blocking
        assert len(result.warnings) > 0
        assert any("assets" in w.lower() for w in result.warnings)
    
    def test_holdings_reconciliation_warning(self):
        """Test that holdings sum mismatch generates warning."""
        content = {
            "fund_name": "Test ETF",
            "series_id": "S000012345",
            "reporting_period_end": "2025-03-31",
            "total_assets": 100000000,
            "holdings": [
                {"ticker": "AAPL", "shares": 1000, "value": 1000000}
                # Sum is only 1M but total_assets is 100M (>5% diff)
            ]
        }
        
        result = self.validator.validate_structure(FilingType.N_PORT, content)
        
        assert result.is_valid is True
        assert len(result.warnings) > 0
        # Should warn about mismatch
        assert any("holdings" in w.lower() or "differ" in w.lower() for w in result.warnings)
    
    def test_ncen_required_fields(self):
        """Test N-CEN has different required fields."""
        content = {
            "fund_name": "Test Fund",
            "series_id": "S000067890",
            "fiscal_year_end": "2024-12-31",
            "total_net_assets": 50000000
        }
        
        result = self.validator.validate_structure(FilingType.N_CEN, content)
        
        assert result.is_valid is True
        assert len(result.missing_fields) == 0
    
    def test_485bpos_required_fields(self):
        """Test 485BPOS prospectus filing requirements."""
        content = {
            "fund_name": "Test Fund",
            "series_id": "S000012345",
            "prospectus_text": "Full prospectus text...",
            "effective_date": "2025-04-01"
        }
        
        result = self.validator.validate_structure(FilingType.FORM_485BPOS, content)
        
        assert result.is_valid is True
    
    def test_validation_report(self):
        """Test detailed validation report."""
        content = {
            "fund_name": "Test ETF",
            # Missing other required fields
        }
        
        report = self.validator.validate_against_rules(FilingType.N_PORT, content)
        
        assert "is_valid" in report
        assert "missing_fields" in report
        assert "required_fields" in report
        assert "fields_present" in report
        
        # Should show what's missing
        assert len(report["missing_fields"]) > 0
        assert "fund_name" in report["fields_present"]


class TestAIValidation:
    """Tests for AI-powered validation (requires API key)."""
    
    @pytest.mark.skip(reason="Requires ANTHROPIC_API_KEY")
    def test_ai_quality_check(self):
        """Test AI-powered quality check."""
        validator = LLMValidator(use_ai=True)
        
        content = {
            "fund_name": "Test ETF",
            "series_id": "S000012345",
            "reporting_period_end": "2020-01-01",  # Very old date
            "total_assets": 100,  # Suspiciously low
            "holdings": []
        }
        
        result = validator.validate_structure(FilingType.N_PORT, content)
        
        # AI should flag issues even though hard validation passes
        assert len(result.warnings) > 0 or result.ai_suggestion is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])