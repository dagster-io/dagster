from unittest import mock

import pytest
from dagster import (
    DagsterInstance,
    DagsterInvariantViolationError,
    PipelineRunStatus,
    RunRequest,
    SensorEvaluationContext,
    SensorExecutionContext,
    build_sensor_context,
    build_run_status_sensor_context,
    run_status_sensor,
    run_failure_sensor,
    sensor,
)
from dagster.core.errors import DagsterInvalidInvocationError
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.test_utils import instance_for_test

from dagster.core.definitions.run_status_sensor_definition import build_run_status_sensor_context_with_dagster_event
from dagster.core.events import (
    DagsterEvent,
    DagsterEventType,
    PipelineFailureData,
)
from dagster.utils.error import SerializableErrorInfo


def test_sensor_context_backcompat():
    # If an instance of SensorEvaluationContext is a SensorExecutionContext, then annotating as
    # SensorExecutionContext and passing in a SensorEvaluationContext should pass mypy
    assert isinstance(SensorEvaluationContext(None, None, None, None, None), SensorExecutionContext)


def test_sensor_invocation_args():

    # Test no arg invocation
    @sensor(pipeline_name="foo_pipeline")
    def basic_sensor_no_arg():
        return RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor_no_arg().run_config == {}

    # Test underscore name
    @sensor(pipeline_name="foo_pipeline")
    def basic_sensor(_):
        return RunRequest(run_key=None, run_config={}, tags={})

    assert basic_sensor(build_sensor_context()).run_config == {}
    assert basic_sensor(None).run_config == {}

    # Test sensor arbitrary arg name
    @sensor(pipeline_name="foo_pipeline")
    def basic_sensor_with_context(_arbitrary_context):
        return RunRequest(run_key=None, run_config={}, tags={})

    context = build_sensor_context()

    # Pass context as positional arg
    assert basic_sensor_with_context(context).run_config == {}

    # pass context as kwarg
    assert basic_sensor_with_context(_arbitrary_context=context).run_config == {}

    # pass context as wrong kwarg
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Sensor invocation expected argument '_arbitrary_context'.",
    ):
        basic_sensor_with_context(  # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
            bad_context=context
        )

    # pass context with no args
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Sensor evaluation function expected context argument, but no context argument was "
        "provided when invoking.",
    ):
        basic_sensor_with_context()  # pylint: disable=no-value-for-parameter

    # pass context with too many args
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Sensor invocation received multiple arguments. Only a first positional context "
        "parameter should be provided when invoking.",
    ):
        basic_sensor_with_context(  # pylint: disable=redundant-keyword-arg
            context, _arbitrary_context=None
        )


def test_instance_access_built_sensor():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to initialize dagster instance, but no instance reference was provided.",
    ):
        build_sensor_context().instance  # pylint: disable=expression-not-assigned

    with instance_for_test() as instance:
        assert isinstance(build_sensor_context(instance).instance, DagsterInstance)


def test_instance_access_with_mock():
    mock_instance = mock.MagicMock(spec=DagsterInstance)
    assert build_sensor_context(instance=mock_instance).instance == mock_instance


def test_build_run_status_sensor_context():
    @run_failure_sensor
    def failure_sensor(context):
        assert context.dagster_event.event_type_value == "PIPELINE_FAILURE"

    ctx = build_run_status_sensor_context(
        sensor_name="failure_sensor",
        dagster_instance=DagsterInstance.ephemeral(),
        pipeline_run_status=PipelineRunStatus.FAILURE,
    )
    failure_sensor(ctx)

    @run_status_sensor(pipeline_run_status=PipelineRunStatus.SUCCESS)
    def status_sensor(context):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"

    ctx = build_run_status_sensor_context(
        sensor_name="status_sensor",
        dagster_instance=DagsterInstance.ephemeral(),
        pipeline_run_status=PipelineRunStatus.SUCCESS,
    )
    status_sensor(ctx)

def test_build_run_status_sensor_context_with_dagster_event():
    @run_failure_sensor
    def failure_sensor(context):
        assert context.dagster_event.event_type_value == "PIPELINE_FAILURE"

    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        pipeline_name="my_unit_test",
        event_specific_data=PipelineFailureData(
            SerializableErrorInfo(message="fail", stack=["fail1", "fail2"], cls_name="unit_test")
        )
    )

    ctx = build_run_status_sensor_context_with_dagster_event(
        sensor_name="failure_sensor",
        dagster_instance=DagsterInstance.ephemeral(),
        dagster_event=dagster_event,
    )
    failure_sensor(ctx.for_run_failure())

    @run_status_sensor(pipeline_run_status=PipelineRunStatus.SUCCESS)
    def status_sensor(context):
        assert context.dagster_event.event_type_value == "PIPELINE_SUCCESS"

    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_SUCCESS.value,
        pipeline_name="my_unit_test",
    )

    ctx = build_run_status_sensor_context_with_dagster_event(
        sensor_name="status_sensor",
        dagster_instance=DagsterInstance.ephemeral(),
        dagster_event=dagster_event
    )
    status_sensor(ctx)
