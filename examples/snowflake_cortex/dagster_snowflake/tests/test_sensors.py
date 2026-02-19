"""Test Dagster sensors."""

from unittest.mock import Mock, patch

from dagster_snowflake_ai.defs.sensors import (
    dynamic_table_freshness_sensor,
)


class TestSensors:
    """Test sensor definitions."""

    def test_dynamic_table_freshness_sensor_configuration(self):
        """Test freshness sensor configuration."""
        assert dynamic_table_freshness_sensor.name == "dynamic_table_freshness_sensor"
        assert dynamic_table_freshness_sensor.minimum_interval_seconds == 60

    def test_dynamic_table_freshness_sensor_with_mock(self, mock_snowflake_resource):
        """Test freshness sensor evaluation with mocked Snowflake."""
        from dagster import SensorEvaluationContext

        mock_context = Mock(spec=SensorEvaluationContext)
        mock_context.log = Mock()

        # Mock the resources dictionary
        with patch(
            "dagster_snowflake.defs.sensors.resources",
            {"snowflake": mock_snowflake_resource},
        ):
            # Configure mock cursor
            mock_cursor = mock_snowflake_resource.get_connection.return_value.__enter__.return_value.cursor.return_value
            mock_cursor.fetchall.return_value = []  # No tables

            result = dynamic_table_freshness_sensor(mock_context)

            # Should return SkipReason
            assert result is not None
