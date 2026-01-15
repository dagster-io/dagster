"""Test partitioned assets."""

from unittest.mock import Mock

from dagster_snowflake_ai.defs.assets.analytics import partitioned_analytics
from dagster_snowflake_ai.defs.assets.ingestion import stories


class TestPartitionedStories:
    """Test partitioned stories ingestion."""

    def test_raw_stories_with_partition(self, mock_snowflake_resource):
        """Test raw_stories asset with partition filtering."""
        mock_context = Mock()
        mock_context.log = Mock()
        mock_context.partition_key = "2024-01-15"

        mock_connection = (
            mock_snowflake_resource.get_connection.return_value.__enter__.return_value
        )
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchone.return_value = (10,)

        result = stories.raw_stories(mock_context, mock_snowflake_resource, Mock())

        assert result is not None
        assert result.metadata["stories_in_staging"].value == 10
        assert mock_cursor.execute.called


class TestPartitionedAnalytics:
    """Test partitioned analytics assets."""

    def test_daily_sentiment_aggregates_with_partition(self, mock_snowflake_resource):
        """Test daily sentiment aggregates with partition."""
        mock_context = Mock()
        mock_context.log = Mock()
        mock_context.partition_key = "2024-01-15"

        mock_connection = (
            mock_snowflake_resource.get_connection.return_value.__enter__.return_value
        )
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchone.return_value = (100, 50, 30, 20, 25, 500.0, 10)

        result = partitioned_analytics.daily_sentiment_aggregates(
            mock_context, mock_snowflake_resource
        )

        assert result is not None
        assert result.metadata["partition_date"].value == "2024-01-15"
        assert result.metadata["total_stories"].value == 100
        assert result.metadata["data_engineering_count"].value == 25

    def test_daily_entity_summary_with_partition(self, mock_snowflake_resource):
        """Test daily entity summary with partition."""
        mock_context = Mock()
        mock_context.log = Mock()
        mock_context.partition_key = "2024-01-15"

        mock_connection = (
            mock_snowflake_resource.get_connection.return_value.__enter__.return_value
        )
        mock_cursor = mock_connection.cursor.return_value
        mock_cursor.fetchone.return_value = (50, 30, 25, 10, 15)

        result = partitioned_analytics.daily_entity_summary(
            mock_context, mock_snowflake_resource
        )

        assert result is not None
        assert result.metadata["partition_date"].value == "2024-01-15"
        assert result.metadata["total_stories"].value == 50
        assert result.metadata["stories_with_skills"].value == 25
