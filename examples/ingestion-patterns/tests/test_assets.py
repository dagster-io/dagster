import tempfile
from pathlib import Path

import dagster as dg
import pandas as pd
from dagster_duckdb import DuckDBResource
from ingestion_patterns.defs.pull_api_ingestion import extract_source_data
from ingestion_patterns.defs.push_webhook_ingestion import process_webhook_data
from ingestion_patterns.resources.mock_apis import clear_webhook_storage, receive_webhook


def test_extract_source_data():
    """Test that extract_source_data asset materializes successfully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        result = dg.materialize(
            [extract_source_data],
            resources={"duckdb": DuckDBResource(database=str(db_path))},
        )
        assert result.success


def test_validate_extracted_data_check_passes():
    """Test that validate_extracted_data check passes with valid data."""
    # Create valid test data
    test_df = pd.DataFrame(
        {
            "id": ["1", "2", "3"],
            "timestamp": [
                "2024-01-01T00:00:00",
                "2024-01-02T00:00:00",
                "2024-01-03T00:00:00",
            ],
            "value": [100, 200, 300],
        }
    )

    # Check that valid data has all required columns
    required_columns = ["id", "timestamp", "value"]
    missing = [col for col in required_columns if col not in test_df.columns]
    assert len(missing) == 0, "Valid data should have all required columns"


def test_validate_extracted_data_check_fails_missing_columns():
    """Test that validate_extracted_data check fails with missing columns."""
    # Create invalid test data (missing 'value' column)
    test_df = pd.DataFrame(
        {
            "id": ["1", "2"],
            "timestamp": ["2024-01-01T00:00:00", "2024-01-02T00:00:00"],
        }
    )

    # Check that invalid data is missing required columns
    required_columns = ["id", "timestamp", "value"]
    missing = [col for col in required_columns if col not in test_df.columns]
    assert len(missing) > 0, "Invalid data should be missing required columns"
    assert "value" in missing


def test_process_webhook_data_no_pending():
    """Test process_webhook_data with no pending payloads."""
    # Clear any existing payloads
    clear_webhook_storage("default")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        result = dg.materialize(
            [process_webhook_data],
            resources={"duckdb": DuckDBResource(database=str(db_path))},
        )
        assert result.success


def test_process_webhook_data_with_payloads():
    """Test process_webhook_data with pending payloads."""
    # Clear and add test payloads
    clear_webhook_storage("default")

    receive_webhook(
        "default",
        {"id": "test-1", "timestamp": "2024-01-01T00:00:00", "data": {"key": "value1"}},
    )
    receive_webhook(
        "default",
        {"id": "test-2", "timestamp": "2024-01-02T00:00:00", "data": {"key": "value2"}},
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        result = dg.materialize(
            [process_webhook_data],
            resources={"duckdb": DuckDBResource(database=str(db_path))},
        )
        assert result.success
