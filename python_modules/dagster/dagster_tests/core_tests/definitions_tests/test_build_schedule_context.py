import pytest
from dagster import (
    DagsterInstance,
    DagsterInvariantViolationError,
    build_schedule_context,
    schedule,
)
from dagster.core.test_utils import instance_for_test


def test_no_arg_schedule_context():
    @schedule(cron_schedule="* * * * *", pipeline_name="no_pipeline")
    def basic_schedule(_):
        return {}

    schedule_data = basic_schedule.evaluate_tick(build_schedule_context())
    assert schedule_data.run_requests[0].run_config == {}


def test_instance_access():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to initialize dagster instance, but no instance reference was provided.",
    ):
        build_schedule_context().instance  # pylint: disable=expression-not-assigned

    with instance_for_test() as instance:
        assert isinstance(build_schedule_context(instance).instance, DagsterInstance)
