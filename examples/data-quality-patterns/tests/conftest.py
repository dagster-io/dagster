"""Pytest configuration and fixtures for data quality tests."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest
from dagster_duckdb import DuckDBResource


@pytest.fixture
def temp_duckdb():
    """Create a temporary DuckDB database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        yield DuckDBResource(database=str(db_path))


@pytest.fixture
def sample_customer_data() -> pd.DataFrame:
    """Sample clean customer data for testing."""
    return pd.DataFrame(
        {
            "customer_id": ["CUST-00001", "CUST-00002", "CUST-00003"],
            "email": ["alice@example.com", "bob@example.com", "carol@example.com"],
            "name": ["Alice Smith", "Bob Johnson", "Carol Williams"],
            "region": ["US", "EU", "APAC"],
            "created_at": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "age": [30, 45, 28],
            "status": ["active", "active", "inactive"],
        }
    )


@pytest.fixture
def sample_customer_data_with_issues() -> pd.DataFrame:
    """Sample customer data with various quality issues for testing."""
    return pd.DataFrame(
        {
            "customer_id": [
                "CUST-00001",
                "CUST-00002",
                "CUST-00001",  # Duplicate (uniqueness)
                "CUST-00004",
            ],
            "email": [
                "alice@example.com",
                None,  # Missing (completeness)
                "invalid-email",  # Invalid format (validity)
                "david@example.com",
            ],
            "name": [
                "Alice Smith",
                "TEST USER",  # Suspicious (accuracy)
                "Carol Williams",
                "N/A",  # Suspicious (accuracy)
            ],
            "region": [
                "US",
                "Europe",  # Inconsistent format (consistency)
                "APAC",
                "US",
            ],
            "created_at": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"],
            "age": [30, 45, 200, 28],  # 200 is invalid (accuracy)
            "status": ["active", "active", "inactive", "active"],
        }
    )


@pytest.fixture
def sample_order_data() -> pd.DataFrame:
    """Sample order data for testing."""
    return pd.DataFrame(
        {
            "order_id": ["ORD-000001", "ORD-000002", "ORD-000003"],
            "customer_id": ["CUST-00001", "CUST-00002", "CUST-00003"],
            "amount": [100.50, 250.00, 75.25],
            "order_date": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "status": ["completed", "pending", "completed"],
        }
    )


@pytest.fixture
def sample_order_data_with_issues() -> pd.DataFrame:
    """Sample order data with quality issues for testing."""
    return pd.DataFrame(
        {
            "order_id": [
                "ORD-000001",
                "ORD-000002",
                "ORD-000001",  # Duplicate (uniqueness)
                "ORD-000004",
            ],
            "customer_id": [
                "CUST-00001",
                "CUST-00002",
                "CUST-INVALID",  # Invalid reference (integrity)
                "CUST-00001",
            ],
            "amount": [
                100.50,
                None,  # Missing (completeness)
                -50.00,  # Negative (validity)
                75.25,
            ],
            "order_date": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"],
            "status": ["completed", "pending", "completed", "pending"],
        }
    )
