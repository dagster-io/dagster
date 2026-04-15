"""Test sensor business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.cli.api.formatters import format_sensor, format_sensors
from dagster_rest_resources.schemas.sensor import (
    DgApiSensor,
    DgApiSensorList,
    DgApiSensorStatus,
    DgApiSensorType,
)


class TestFormatSensors:
    """Test the sensor formatting functions."""

    def _create_sample_sensor_list(self):
        """Create sample DgApiSensorList for testing."""
        sensors = [
            DgApiSensor(
                id="sensor1-id",
                name="daily_sensor",
                status=DgApiSensorStatus.RUNNING,
                sensor_type=DgApiSensorType.STANDARD,
                description="Daily processing sensor",
                repository_origin="main_location@main_repo",
                next_tick_timestamp=1705311000.0,  # 2024-01-15T10:30:00Z
            ),
            DgApiSensor(
                id="sensor2-id",
                name="asset_sensor",
                status=DgApiSensorStatus.STOPPED,
                sensor_type=DgApiSensorType.ASSET,
                description="Asset change sensor",
                repository_origin="main_location@main_repo",
                next_tick_timestamp=None,
            ),
            DgApiSensor(
                id="sensor3-id",
                name="minimal_sensor",
                status=DgApiSensorStatus.PAUSED,
                sensor_type=DgApiSensorType.MULTI_ASSET,
                description=None,
                repository_origin=None,
                next_tick_timestamp=None,
            ),
        ]
        return DgApiSensorList(items=sensors, total=len(sensors))

    def _create_sample_sensor(self):
        """Create sample DgApiSensor for testing."""
        return DgApiSensor(
            id="single-sensor-id",
            name="critical_sensor",
            status=DgApiSensorStatus.RUNNING,
            sensor_type=DgApiSensorType.AUTO_MATERIALIZE,
            description="Critical production sensor",
            repository_origin="prod_location@prod_repo",
            next_tick_timestamp=1705311900.0,  # 2024-01-15T10:45:00Z
        )

    def test_format_sensors_text_output(self, snapshot):
        """Test formatting sensors as text."""
        from dagster_shared.utils.timing import fixed_timezone

        sensor_list = self._create_sample_sensor_list()
        with fixed_timezone("UTC"):
            result = format_sensors(sensor_list, as_json=False)

        # Snapshot the entire text output
        snapshot.assert_match(result)

    def test_format_sensors_json_output(self, snapshot):
        """Test formatting sensors as JSON."""
        sensor_list = self._create_sample_sensor_list()
        result = format_sensors(sensor_list, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_sensor_text_output(self, snapshot):
        """Test formatting single sensor as text."""
        from dagster_shared.utils.timing import fixed_timezone

        sensor = self._create_sample_sensor()
        with fixed_timezone("UTC"):
            result = format_sensor(sensor, as_json=False)

        # Snapshot the text output
        snapshot.assert_match(result)

    def test_format_sensor_json_output(self, snapshot):
        """Test formatting single sensor as JSON."""
        sensor = self._create_sample_sensor()
        result = format_sensor(sensor, as_json=True)

        # For JSON, we want to snapshot the parsed structure to avoid formatting differences
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_format_minimal_sensor_text_output(self, snapshot):
        """Test formatting minimal sensor as text."""
        from dagster_shared.utils.timing import fixed_timezone

        sensor = DgApiSensor(
            id="minimal-id",
            name="minimal_sensor",
            status=DgApiSensorStatus.PAUSED,
            sensor_type=DgApiSensorType.STANDARD,
            description=None,
            repository_origin=None,
            next_tick_timestamp=None,
        )
        with fixed_timezone("UTC"):
            result = format_sensor(sensor, as_json=False)

        snapshot.assert_match(result)

    def test_format_minimal_sensor_json_output(self, snapshot):
        """Test formatting minimal sensor as JSON."""
        sensor = DgApiSensor(
            id="minimal-id",
            name="minimal_sensor",
            status=DgApiSensorStatus.PAUSED,
            sensor_type=DgApiSensorType.STANDARD,
            description=None,
            repository_origin=None,
            next_tick_timestamp=None,
        )
        result = format_sensor(sensor, as_json=True)

        parsed = json.loads(result)
        snapshot.assert_match(parsed)
