"""Test sensor business logic functions without mocks.

These tests focus on testing pure functions that process data without requiring
GraphQL client mocking or external dependencies.
"""

import json

from dagster_dg_cli.api_layer.graphql_adapter.sensor import (
    process_repositories_response,
    process_sensor_response,
    process_sensors_response,
)
from dagster_dg_cli.api_layer.schemas.sensor import (
    DgApiSensor,
    DgApiSensorList,
    DgApiSensorStatus,
    DgApiSensorType,
)
from dagster_dg_cli.cli.api.sensor import format_sensor, format_sensors


class TestProcessSensorResponses:
    """Test the pure functions that process GraphQL responses."""

    def test_process_sensors_response_success(self, snapshot):
        """Test processing a successful sensors GraphQL response."""
        # Sample GraphQL response structure
        response = {
            "sensorsOrError": {
                "__typename": "Sensors",
                "results": [
                    {
                        "id": "sensor1-id",
                        "name": "daily_sensor",
                        "sensorState": {"status": "RUNNING"},
                        "sensorType": "STANDARD",
                        "description": "Daily processing sensor",
                    },
                    {
                        "id": "sensor2-id",
                        "name": "asset_sensor",
                        "sensorState": {"status": "STOPPED"},
                        "sensorType": "ASSET",
                        "description": "Asset change sensor",
                    },
                ],
            }
        }
        result = process_sensors_response(response)

        # Snapshot the entire result to capture structure and data
        snapshot.assert_match(result)

    def test_process_sensors_response_empty(self, snapshot):
        """Test processing an empty sensors GraphQL response."""
        response = {"sensorsOrError": {"__typename": "Sensors", "results": []}}
        result = process_sensors_response(response)

        # Snapshot empty result
        snapshot.assert_match(result)

    def test_process_sensors_response_missing_key(self, snapshot):
        """Test processing a response missing the sensorsOrError key."""
        malformed_response = {}
        try:
            result = process_sensors_response(malformed_response)
            # If no exception, snapshot the result
            snapshot.assert_match(result)
        except Exception as e:
            # Snapshot the error message
            snapshot.assert_match({"error": str(e)})

    def test_process_sensors_response_error_typename(self, snapshot):
        """Test processing a sensors response with error typename."""
        error_response = {
            "sensorsOrError": {
                "__typename": "RepositoryNotFoundError",
                "message": "Repository not found",
            }
        }
        try:
            result = process_sensors_response(error_response)
            snapshot.assert_match(result)
        except Exception as e:
            snapshot.assert_match({"error": str(e)})

    def test_process_repositories_response_success(self, snapshot):
        """Test processing a successful repositories GraphQL response."""
        response = {
            "repositoriesOrError": {
                "__typename": "RepositoryConnection",
                "nodes": [
                    {
                        "name": "main_repo",
                        "location": {"name": "main_location"},
                        "sensors": [
                            {
                                "id": "sensor1-id",
                                "name": "daily_sensor",
                                "sensorState": {"status": "RUNNING"},
                                "sensorType": "STANDARD",
                                "description": "Daily processing sensor",
                            },
                            {
                                "id": "sensor2-id",
                                "name": "asset_sensor",
                                "sensorState": {"status": "PAUSED"},
                                "sensorType": "MULTI_ASSET",
                                "description": "Asset change sensor",
                            },
                        ],
                    },
                    {
                        "name": "secondary_repo",
                        "location": {"name": "secondary_location"},
                        "sensors": [
                            {
                                "id": "sensor3-id",
                                "name": "hourly_sensor",
                                "sensorState": {"status": "STOPPED"},
                                "sensorType": "FRESHNESS_POLICY",
                                "description": None,
                            }
                        ],
                    },
                ],
            }
        }
        result = process_repositories_response(response)

        # Snapshot the entire result to capture structure and data
        snapshot.assert_match(result)

    def test_process_repositories_response_empty(self, snapshot):
        """Test processing an empty repositories GraphQL response."""
        response = {"repositoriesOrError": {"__typename": "RepositoryConnection", "nodes": []}}
        result = process_repositories_response(response)

        snapshot.assert_match(result)

    def test_process_sensor_response_success(self, snapshot):
        """Test processing a successful single sensor GraphQL response."""
        response = {
            "sensorOrError": {
                "__typename": "Sensor",
                "id": "single-sensor-id",
                "name": "critical_sensor",
                "sensorState": {"status": "RUNNING"},
                "sensorType": "AUTO_MATERIALIZE",
                "description": "Critical production sensor",
            }
        }
        result = process_sensor_response(response)

        snapshot.assert_match(result)

    def test_process_sensor_response_not_found_error(self, snapshot):
        """Test processing a sensor not found error."""
        error_response = {
            "sensorOrError": {
                "__typename": "SensorNotFoundError",
                "message": "Sensor 'nonexistent_sensor' not found",
            }
        }
        try:
            result = process_sensor_response(error_response)
            snapshot.assert_match(result)
        except Exception as e:
            snapshot.assert_match({"error": str(e)})


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


class TestSensorDataProcessing:
    """Test processing of sensor data structures.

    This class tests pure functions and domain model functionality
    without requiring external dependencies.
    """

    def test_sensor_creation_with_all_fields(self, snapshot):
        """Test creating sensor with all possible fields."""
        sensor = DgApiSensor(
            id="complete-sensor-xyz",
            name="comprehensive_sensor",
            status=DgApiSensorStatus.RUNNING,
            sensor_type=DgApiSensorType.FRESHNESS_POLICY,
            description="Comprehensive test sensor with all fields",
            repository_origin="test_location@test_repo",
            next_tick_timestamp=1705311000.0,
        )

        # Test JSON serialization works correctly
        result = sensor.model_dump_json(indent=2)
        parsed = json.loads(result)
        snapshot.assert_match(parsed)

    def test_sensor_status_enum_values(self):
        """Test that all expected SensorStatus enum values are available."""
        expected_statuses = ["RUNNING", "STOPPED", "PAUSED"]

        actual_statuses = [status.value for status in DgApiSensorStatus]
        assert set(actual_statuses) == set(expected_statuses)

    def test_sensor_type_enum_values(self):
        """Test that all expected SensorType enum values are available."""
        expected_types = [
            "STANDARD",
            "MULTI_ASSET",
            "FRESHNESS_POLICY",
            "AUTO_MATERIALIZE",
            "ASSET",
        ]

        actual_types = [sensor_type.value for sensor_type in DgApiSensorType]
        assert set(actual_types) == set(expected_types)

    def test_sensor_with_missing_optional_fields(self):
        """Test sensor creation with None values for optional fields."""
        sensor = DgApiSensor(
            id="sparse-sensor-123",
            name="sparse_sensor",
            status=DgApiSensorStatus.STOPPED,
            sensor_type=DgApiSensorType.STANDARD,
            description=None,
            repository_origin=None,
            next_tick_timestamp=None,
        )

        assert sensor.id == "sparse-sensor-123"
        assert sensor.name == "sparse_sensor"
        assert sensor.status == DgApiSensorStatus.STOPPED
        assert sensor.sensor_type == DgApiSensorType.STANDARD
        assert sensor.description is None
        assert sensor.repository_origin is None
        assert sensor.next_tick_timestamp is None

    def test_sensor_list_creation(self):
        """Test SensorList creation and basic functionality."""
        sensors = [
            DgApiSensor(
                id="sensor1",
                name="first_sensor",
                status=DgApiSensorStatus.RUNNING,
                sensor_type=DgApiSensorType.STANDARD,
            ),
            DgApiSensor(
                id="sensor2",
                name="second_sensor",
                status=DgApiSensorStatus.PAUSED,
                sensor_type=DgApiSensorType.ASSET,
            ),
        ]
        sensor_list = DgApiSensorList(items=sensors, total=len(sensors))

        assert len(sensor_list.items) == 2
        assert sensor_list.total == 2
        assert sensor_list.items[0].name == "first_sensor"
        assert sensor_list.items[1].name == "second_sensor"

    def test_sensor_timestamp_handling(self, snapshot):
        """Test sensor with various timestamp values."""
        test_cases = [
            # Normal timestamp
            DgApiSensor(
                id="sensor1",
                name="normal_timestamp",
                status=DgApiSensorStatus.RUNNING,
                sensor_type=DgApiSensorType.STANDARD,
                next_tick_timestamp=1705311000.0,
            ),
            # No timestamp
            DgApiSensor(
                id="sensor2",
                name="no_timestamp",
                status=DgApiSensorStatus.STOPPED,
                sensor_type=DgApiSensorType.STANDARD,
                next_tick_timestamp=None,
            ),
            # Future timestamp
            DgApiSensor(
                id="sensor3",
                name="future_timestamp",
                status=DgApiSensorStatus.PAUSED,
                sensor_type=DgApiSensorType.STANDARD,
                next_tick_timestamp=2000000000.0,  # Far future
            ),
        ]

        results = []
        for sensor in test_cases:
            # Test serialization
            serialized = json.loads(sensor.model_dump_json())
            results.append(serialized)

        snapshot.assert_match(results)
