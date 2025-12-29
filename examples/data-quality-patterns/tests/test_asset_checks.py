"""Tests for asset checks that verify quality issues are detected."""

import tempfile
from pathlib import Path

import dagster as dg
from dagster_duckdb import DuckDBResource
from data_quality_patterns.defs.assets.python_checks import (
    check_accuracy_names,
    check_completeness_email,
    check_consistency_region,
    check_integrity_customer_ref,
    check_uniqueness_customer_id,
    check_validity_email,
)
from data_quality_patterns.defs.assets.raw_data import raw_customers


def test_raw_data_generates_with_issues():
    """Test that raw data generation includes quality issues."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        result = dg.materialize(
            [raw_customers],
            resources={"duckdb": DuckDBResource(database=str(db_path))},
        )

        assert result.success, "Raw data materialization should succeed"

        # Get the output DataFrame
        df = result.output_for_node("raw_customers")
        assert len(df) > 0

        # Verify some quality issues exist (due to failure_rate)
        # At least one of these should have issues
        has_null_emails = df["email"].isna().any()
        has_duplicates = df["customer_id"].duplicated().any()

        # With seed=42 and failure_rate=0.15, we expect some issues
        assert has_null_emails or has_duplicates, "Expected quality issues in generated data"


def test_check_detects_uniqueness_issues(sample_customer_data_with_issues):
    """Test that uniqueness check detects duplicate IDs."""
    # The fixture has duplicate customer_id values
    result = check_uniqueness_customer_id(None, sample_customer_data_with_issues)

    assert not result.passed, "Check should fail due to duplicate IDs"
    assert "duplicate" in result.description.lower()


def test_check_detects_completeness_issues(sample_customer_data_with_issues):
    """Test that completeness check detects missing emails."""
    # The fixture has null email values
    result = check_completeness_email(None, sample_customer_data_with_issues)

    # Completeness is 75% (3/4), below 95% threshold
    assert not result.passed, "Check should fail due to missing emails"


def test_check_detects_validity_issues(sample_customer_data_with_issues):
    """Test that validity check detects invalid email formats."""
    result = check_validity_email(None, sample_customer_data_with_issues)

    # Only 2 of 4 emails are valid format (50%), below 90% threshold
    assert not result.passed, "Check should fail due to invalid emails"


def test_check_detects_accuracy_issues(sample_customer_data_with_issues):
    """Test that accuracy check detects suspicious names."""
    result = check_accuracy_names(None, sample_customer_data_with_issues)

    # The fixture has "TEST USER" and "N/A" names
    assert not result.passed, "Check should fail due to suspicious names"


def test_check_detects_consistency_issues(sample_customer_data_with_issues):
    """Test that consistency check detects non-standard region codes."""
    result = check_consistency_region(None, sample_customer_data_with_issues)

    # The fixture has "Europe" instead of "EU"
    assert not result.passed, "Check should fail due to inconsistent region"


def test_check_detects_integrity_issues(sample_customer_data, sample_order_data_with_issues):
    """Test that integrity check detects invalid foreign key references."""
    result = check_integrity_customer_ref(None, sample_order_data_with_issues, sample_customer_data)

    # The fixture has "CUST-INVALID" which doesn't exist in customers
    assert not result.passed, "Check should fail due to invalid customer reference"


def test_check_passes_with_clean_data(sample_customer_data):
    """Test that checks pass with clean data."""
    # All checks should pass with clean data
    assert check_accuracy_names(None, sample_customer_data).passed
    assert check_completeness_email(None, sample_customer_data).passed
    assert check_validity_email(None, sample_customer_data).passed
    assert check_uniqueness_customer_id(None, sample_customer_data).passed
    assert check_consistency_region(None, sample_customer_data).passed
