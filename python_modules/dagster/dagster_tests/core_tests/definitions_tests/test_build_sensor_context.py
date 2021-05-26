import pytest
from dagster import (
    DagsterInstance,
    DagsterInvariantViolationError,
    RunRequest,
    build_sensor_context,
    sensor,
)
from dagster.core.test_utils import instance_for_test


def test_basic_sensor_context():
    @sensor(pipeline_name="foo_pipeline")
    def basic_sensor(_):
        return RunRequest(run_key=None, run_config={}, tags={})

    sensor_data = basic_sensor.evaluate_tick(build_sensor_context())
    assert sensor_data.run_requests[0].run_config == {}


def test_instance_access():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to initialize dagster instance, but no instance reference was provided.",
    ):
        build_sensor_context().instance  # pylint: disable=expression-not-assigned

    with instance_for_test() as instance:
        assert isinstance(build_sensor_context(instance).instance, DagsterInstance)
