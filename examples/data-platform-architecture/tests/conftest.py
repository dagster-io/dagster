"""Pytest configuration and fixtures for data platform architecture guide tests."""

# Add project root to path for imports
import sys
from pathlib import Path

import pandas as pd
import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_sales_data() -> pd.DataFrame:
    """Fixture providing sample sales data for testing."""
    return pd.DataFrame(
        {
            "sale_id": ["S001", "S002", "S003"],
            "product_id": ["P001", "P002", "P003"],
            "amount": [100.0, 200.0, 150.0],
            "date": ["2025-01-01", "2025-01-02", "2025-01-03"],
        }
    )


@pytest.fixture
def sample_clickstream_data() -> pd.DataFrame:
    """Fixture providing sample clickstream data for testing."""
    return pd.DataFrame(
        {
            "event_id": ["E001", "E002", "E003"],
            "user_id": ["U001", "U002", "U003"],
            "event_type": ["click", "view", "purchase"],
            "timestamp": ["2025-01-01 10:00:00", "2025-01-01 10:05:00", "2025-01-01 10:10:00"],
        }
    )
