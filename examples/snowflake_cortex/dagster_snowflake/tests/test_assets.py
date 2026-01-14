"""Test Dagster assets."""

from unittest.mock import Mock

from dagster_snowflake_ai.defs.assets.cortex_ai import (
    aggregations,
    entity_extraction,
    sentiment_analysis,
)
from dagster_snowflake_ai.defs.assets.ingestion import stories


class TestStoriesAsset:
    """Test stories ingestion asset."""

    def test_raw_stories_with_mock(self, mock_snowflake_resource):
        """Test raw_stories asset with mocked Snowflake."""
        mock_context = Mock()
        mock_context.log = Mock()
        mock_context.partition_key = "2024-01-15"

        mock_connection = (
            mock_snowflake_resource.get_connection.return_value.__enter__.return_value
        )
        mock_cursor = mock_connection.cursor.return_value
        expected_story_count = 10
        mock_cursor.fetchone.return_value = (expected_story_count,)

        result = stories.raw_stories(mock_context, mock_snowflake_resource)

        assert result is not None
        assert result.metadata["stories_in_staging"].value == expected_story_count
        assert result.metadata["table_schema"].value.endswith(".stories")
        assert mock_cursor.execute.called


class TestSentimentAnalysisAsset:
    """Test sentiment analysis asset."""

    def test_story_sentiment_analysis_with_mock(self, mock_snowflake_resource):
        """Test sentiment analysis asset with mocked Snowflake."""
        mock_context = Mock()
        mock_context.log = Mock()
        mock_context.partition_key = "2024-01-15"

        # Configure mock cursor
        mock_cursor = mock_snowflake_resource.get_connection.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchone.return_value = (
            10,
            3,
            500.0,
        )  # stories, posters, avg_length

        result = sentiment_analysis.story_sentiment_analysis(
            mock_context, mock_snowflake_resource
        )

        assert result is not None
        assert result.metadata["stories_processed"].value == 10
        assert result.metadata["unique_posters"].value == 3
        assert result.metadata["avg_description_length"].value == 500.0
        assert result.metadata["cortex_function"].value == "AI_CLASSIFY"


class TestEntityExtractionAsset:
    """Test entity extraction asset."""

    def test_entity_extraction_with_mock(self, mock_snowflake_resource):
        """Test entity extraction asset with mocked Snowflake."""
        mock_context = Mock()
        mock_context.log = Mock()
        mock_context.partition_key = "2024-01-15"

        mock_connection = (
            mock_snowflake_resource.get_connection.return_value.__enter__.return_value
        )
        mock_cursor = mock_connection.cursor.return_value
        expected_stories_with_entities = 5
        mock_cursor.fetchone.return_value = (expected_stories_with_entities,)

        result = entity_extraction.entity_extraction(
            mock_context, mock_snowflake_resource
        )

        assert result is not None
        assert (
            result.metadata["stories_with_entities"].value
            == expected_stories_with_entities
        )
        assert result.metadata["model_used"].value == "llama3.1-8b"
        assert result.metadata["cortex_function"].value == "SNOWFLAKE.CORTEX.COMPLETE"


class TestAggregationsAsset:
    """Test aggregations asset."""

    def test_daily_story_summary_with_mock(self, mock_snowflake_resource):
        """Test daily story summary asset with mocked Snowflake."""
        mock_context = Mock()
        mock_context.log = Mock()
        mock_context.partition_key = "2024-01-15"

        mock_connection = (
            mock_snowflake_resource.get_connection.return_value.__enter__.return_value
        )
        mock_cursor = mock_connection.cursor.return_value
        expected_summary_count = 3
        mock_cursor.fetchone.return_value = (expected_summary_count,)

        result = aggregations.daily_story_summary(mock_context, mock_snowflake_resource)

        assert result is not None
        assert result.metadata["summary_count"].value == expected_summary_count
        assert "dagster_value" in result.metadata
