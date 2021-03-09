from dagster import execute_pipeline
from docs_snippets.concepts.partitions_schedules_sensors.sensor_alert import failure_alert_pipeline


def test_failure_alert_pipeline():
    result = execute_pipeline(failure_alert_pipeline, mode="test")
    assert result.success
