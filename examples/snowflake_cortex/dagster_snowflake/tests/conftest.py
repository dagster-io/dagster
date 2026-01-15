"""Pytest configuration and fixtures."""

from unittest.mock import MagicMock, Mock

import pytest

try:
    from dagster_snowflake import SnowflakeResource
except ImportError:
    SnowflakeResource = None

requires_snowflake = pytest.mark.skipif(
    SnowflakeResource is None,
    reason="dagster-snowflake package not available",
)


@pytest.fixture
@requires_snowflake
def mock_snowflake_resource():
    """Create a mock Snowflake resource for testing."""
    mock_resource = Mock(spec=SnowflakeResource)
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_resource.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
    mock_resource.get_connection.return_value.__exit__ = Mock(return_value=None)
    return mock_resource


@pytest.fixture
def sample_news_data():
    """Sample news article data for testing."""
    return [
        {
            "article_id": "test_001",
            "headline": "Test Headline",
            "content": "Test content for sentiment analysis",
            "published_at": "2024-01-01 10:00:00",
            "source": "test_source",
        }
    ]


@pytest.fixture
def sample_sentiment_data():
    """Sample sentiment analysis results."""
    return {
        "articles_processed": 10,
        "unique_sources": 3,
        "avg_content_length": 500.0,
    }
