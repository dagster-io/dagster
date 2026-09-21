import time

import dagster._check as check
import pytest
from dagster._core.events import (
    DagsterEvent,
    DagsterEventType,
    EngineEventData,
    HookErroredData,
    JobCanceledData,
    JobFailureData,
)
from dagster._core.events.log import EventLogEntry
from dagster._core.execution.plan.objects import StepFailureData, StepRetryData, UserFailureData
from dagster._core.test_utils import environ
from dagster._serdes import serialize_value
from dagster._utils.error import SerializableErrorInfo
from dagster_cloud.storage.event_logs.utils import (
    _get_maximum_event_message_characters,
    truncate_event,
)

BIG_STACK_TRACE = SerializableErrorInfo(
    message="Error occurred",
    stack=["a" * 100000],
    cls_name="Exception",
    cause=None,
)


def test_truncate_event():
    event = EventLogEntry(
        error_info=None,
        user_message="foobar",
        level="debug",
        run_id="foo",
        timestamp=time.time(),
        dagster_event=None,
    )
    assert truncate_event(event) == event

    event = EventLogEntry(
        error_info=None,
        level="debug",
        user_message="a" * 100000,
        run_id="foo",
        timestamp=time.time(),
        dagster_event=None,
    )
    truncated_event = truncate_event(event)
    assert len(truncated_event.user_message) < _get_maximum_event_message_characters() + 100
    assert truncated_event.user_message.startswith("[TRUNCATED")
    assert truncated_event.user_message.endswith("aaa [TRUNCATED]")


@pytest.fixture
def error_size():
    with environ({"DAGSTER_CLOUD_MAXIMUM_EVENT_ERROR_SIZE": "1000"}):
        yield 1000


@pytest.mark.parametrize(
    "event_type,event_specific_data,expected_truncations",
    [
        (
            DagsterEventType.STEP_FAILURE,
            StepFailureData(
                error=BIG_STACK_TRACE,
                user_failure_data=UserFailureData(label="K8sError"),
            ),
            ["stack"],
        ),
        (
            DagsterEventType.RUN_FAILURE,
            JobFailureData(
                error=BIG_STACK_TRACE,
                first_step_failure_event=DagsterEvent(
                    event_type_value="STEP_FAILURE",
                    job_name="my_job",
                    step_key="my_op",
                    message="Job failed",
                    event_specific_data=StepFailureData(
                        error=BIG_STACK_TRACE,
                        user_failure_data=UserFailureData(label="K8sError"),
                    ),
                ),
            ),
            ["stack", "stack"],
        ),
        (
            DagsterEventType.ENGINE_EVENT,
            EngineEventData(
                error=BIG_STACK_TRACE,
                marker_start=None,
                marker_end=None,
            ),
            ["stack"],
        ),
        (
            DagsterEventType.RUN_CANCELED,
            JobCanceledData(
                error=BIG_STACK_TRACE,
            ),
            ["stack"],
        ),
        (
            DagsterEventType.HOOK_ERRORED,
            HookErroredData(
                error=BIG_STACK_TRACE,
            ),
            ["stack"],
        ),
        (
            DagsterEventType.STEP_UP_FOR_RETRY,
            StepRetryData(
                error=BIG_STACK_TRACE,
                seconds_to_wait=10,
            ),
            ["stack"],
        ),
    ],
)
def test_truncated_event_errors(error_size, event_type, event_specific_data, expected_truncations):
    event = EventLogEntry(
        error_info=None,
        level="error",
        user_message="Job failed",
        run_id="foo",
        timestamp=time.time(),
        dagster_event=DagsterEvent(
            event_type_value=event_type.value,
            job_name="my_job",
            step_key="my_op",
            message="Job failed",
            event_specific_data=event_specific_data,
        ),
    )

    error = check.not_none(check.not_none(event.dagster_event).event_specific_data.error)  # type:ignore
    assert len(serialize_value(error)) > error_size

    truncations = []
    truncated_event = truncate_event(event, truncations=truncations)
    assert truncations == expected_truncations

    truncated_error = check.not_none(
        check.not_none(truncated_event.dagster_event).event_specific_data.error  # type:ignore
    )
    assert len(serialize_value(truncated_error)) < error_size + 100

    if event_type == DagsterEventType.RUN_FAILURE:
        error = event.dagster_event.event_specific_data.first_step_failure_event.event_specific_data.error  # type:ignore
        assert len(serialize_value(error)) > error_size

        truncated_event = truncate_event(event)

        truncated_error = truncated_event.dagster_event.event_specific_data.first_step_failure_event.event_specific_data.error  # type:ignore

        assert len(serialize_value(truncated_error)) < error_size + 100
