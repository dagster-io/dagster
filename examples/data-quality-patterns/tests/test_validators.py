"""Tests for reusable validation components."""

import pandas as pd
import pytest
from data_quality_patterns.lib.quality_metrics import (
    calculate_completeness,
    calculate_quality_score,
    calculate_uniqueness,
    calculate_validity,
)
from data_quality_patterns.lib.validators import (
    check_age_range,
    check_required_fields,
    check_uniqueness,
    clean_dataframe,
    validate_email_format,
)


def test_validate_email_format_valid():
    """Test email validation with valid emails."""
    df = pd.DataFrame(
        {
            "email": ["valid@example.com", "another.valid@test.org"],
            "customer_id": ["001", "002"],
        }
    )

    invalid_records, errors = validate_email_format(df, "email")
    assert invalid_records.empty
    assert len(errors) == 0


def test_validate_email_format_invalid():
    """Test email validation with invalid emails."""
    df = pd.DataFrame(
        {
            "email": ["valid@example.com", "invalid-email", "missing@domain"],
            "customer_id": ["001", "002", "003"],
        }
    )

    invalid_records, errors = validate_email_format(df, "email")
    assert len(invalid_records) == 2
    assert len(errors) > 0


def test_check_required_fields_present():
    """Test required fields check when all fields present."""
    df = pd.DataFrame({"customer_id": ["001"], "email": ["test@example.com"]})

    errors = check_required_fields(df, ["customer_id", "email"])
    assert len(errors) == 0


def test_check_required_fields_missing():
    """Test required fields check when fields are missing."""
    df = pd.DataFrame({"customer_id": ["001"], "name": ["Test"]})

    errors = check_required_fields(df, ["customer_id", "email"])
    assert len(errors) > 0
    assert "email" in errors[0]


def test_check_uniqueness_unique():
    """Test uniqueness check with unique values."""
    df = pd.DataFrame(
        {
            "customer_id": ["001", "002", "003"],
        }
    )

    duplicate_records, errors = check_uniqueness(df, ["customer_id"])
    assert duplicate_records.empty
    assert len(errors) == 0


def test_check_uniqueness_duplicates():
    """Test uniqueness check with duplicates."""
    df = pd.DataFrame(
        {
            "customer_id": ["001", "002", "001"],
        }
    )

    duplicate_records, errors = check_uniqueness(df, ["customer_id"])
    assert len(duplicate_records) == 2  # Both duplicated rows
    assert len(errors) > 0


def test_check_age_range_valid():
    """Test age range validation with valid ages."""
    df = pd.DataFrame(
        {
            "age": [25, 30, 45],
            "customer_id": ["001", "002", "003"],
        }
    )

    invalid_records, warnings = check_age_range(df, "age", 0, 120, "customer_id")
    assert invalid_records.empty
    assert len(warnings) == 0


def test_check_age_range_invalid():
    """Test age range validation with invalid ages."""
    df = pd.DataFrame(
        {
            "age": [25, 200, -5],
            "customer_id": ["001", "002", "003"],
        }
    )

    invalid_records, warnings = check_age_range(df, "age", 0, 120, "customer_id")
    assert len(invalid_records) == 2
    assert len(warnings) > 0


def test_clean_dataframe():
    """Test dataframe cleaning removes invalid records."""
    df = pd.DataFrame(
        {
            "customer_id": ["001", "002", "001"],
            "email": ["valid@test.com", "invalid-email", "valid2@test.com"],
            "created_at": ["2025-01-01", "invalid-date", "2025-01-03"],
        }
    )

    cleaned = clean_dataframe(df)
    assert len(cleaned) < len(df)
    assert cleaned["customer_id"].is_unique


def test_calculate_completeness():
    """Test completeness metric calculation."""
    df = pd.DataFrame(
        {
            "email": ["a@test.com", "b@test.com", None],
        }
    )

    completeness = calculate_completeness(df, "email")
    assert completeness == pytest.approx(0.666, abs=0.01)


def test_calculate_validity():
    """Test validity metric calculation."""
    df = pd.DataFrame(
        {
            "email": ["valid@test.com", "invalid-email", "valid2@test.com"],
        }
    )

    validity = calculate_validity(df, "email")
    assert validity == pytest.approx(0.666, abs=0.01)


def test_calculate_uniqueness():
    """Test uniqueness metric calculation."""
    df = pd.DataFrame(
        {
            "customer_id": ["001", "002", "001"],
        }
    )

    uniqueness = calculate_uniqueness(df, "customer_id")
    assert uniqueness == pytest.approx(0.666, abs=0.01)


def test_calculate_quality_score():
    """Test overall quality score calculation."""
    df = pd.DataFrame(
        {
            "customer_id": ["001", "002", "003"],
            "email": ["a@test.com", "b@test.com", "c@test.com"],
            "created_at": ["2025-01-01", "2025-01-02", "2025-01-03"],
        }
    )

    metrics = calculate_quality_score(df)
    assert metrics.quality_score >= 0.0
    assert metrics.quality_score <= 1.0
    assert metrics.completeness == 1.0
    assert metrics.validity == 1.0
    assert metrics.uniqueness == 1.0

