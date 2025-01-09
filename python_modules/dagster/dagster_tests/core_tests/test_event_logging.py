import logging
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Callable

from dagster import DagsterEvent, execute_job, job, op
from dagster._core.definitions.events import DynamicOutput
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.node_definition import NodeDefinition
from dagster._core.definitions.output import DynamicOut
from dagster._core.definitions.reconstruct import reconstructable
from dagster._core.events import DagsterEventType
from dagster._core.events.log import EventLogEntry, construct_event_logger
from dagster._core.test_utils import instance_for_test
from dagster._loggers import colored_console_logger
from dagster._serdes import deserialize_value


def get_loggers(event_callback):
    return {
        "callback": construct_event_logger(event_callback),
        "console": colored_console_logger,
    }


def single_dagster_event(
    events: Mapping[DagsterEventType, Sequence[DagsterEvent]], event_type: DagsterEventType
) -> DagsterEvent:
    assert event_type in events
    return events[event_type][0]


def define_event_logging_job(
    name: str,
    node_defs: Sequence[NodeDefinition],
    event_callback: Callable[[EventLogEntry], None],
    deps=None,
) -> JobDefinition:
    return JobDefinition(
        graph_def=GraphDefinition(
            name=name,
            node_defs=node_defs,
            dependencies=deps,
        ),
        logger_defs=get_loggers(event_callback),
    )


def test_empty_job():
    events = defaultdict(list)

    def _event_callback(record):
        assert isinstance(record, EventLogEntry)
        if record.is_dagster_event:
            events[record.dagster_event.event_type].append(record)  # pyright: ignore[reportOptionalMemberAccess]

    job_def = JobDefinition(
        graph_def=GraphDefinition(
            name="empty_job",
            node_defs=[],
        ),
        logger_defs=get_loggers(_event_callback),
    )

    result = job_def.execute_in_process({"loggers": {"callback": {}, "console": {}}})
    assert result.success
    assert events

    assert single_dagster_event(events, DagsterEventType.PIPELINE_START).job_name == "empty_job"
    assert single_dagster_event(events, DagsterEventType.PIPELINE_SUCCESS).job_name == "empty_job"


def test_single_op_job_success():
    events = defaultdict(list)

    @op
    def op_one():
        return 1

    def _event_callback(record):
        if record.is_dagster_event:
            events[record.dagster_event.event_type].append(record)

    job_def = JobDefinition(
        graph_def=GraphDefinition(
            name="single_op_job",
            node_defs=[op_one],
        ),
        logger_defs=get_loggers(_event_callback),
        tags={"foo": "bar"},
    )

    result = job_def.execute_in_process({"loggers": {"callback": {}}})
    assert result.success
    assert events

    start_event = single_dagster_event(events, DagsterEventType.STEP_START)
    assert start_event.job_name == "single_op_job"
    assert start_event.dagster_event.node_name == "op_one"  # pyright: ignore[reportAttributeAccessIssue]

    # persisted logging tags contain pipeline_name but not pipeline_tags
    assert start_event.dagster_event.logging_tags["job_name"] == "single_op_job"  # pyright: ignore[reportAttributeAccessIssue]
    assert "pipeline_tags" not in start_event.dagster_event.logging_tags  # pyright: ignore[reportAttributeAccessIssue]

    output_event = single_dagster_event(events, DagsterEventType.STEP_OUTPUT)
    assert output_event
    assert output_event.dagster_event.step_output_data.output_name == "result"  # pyright: ignore[reportAttributeAccessIssue]

    success_event = single_dagster_event(events, DagsterEventType.STEP_SUCCESS)
    assert success_event.job_name == "single_op_job"
    assert success_event.dagster_event.node_name == "op_one"  # pyright: ignore[reportAttributeAccessIssue]

    assert isinstance(success_event.dagster_event.step_success_data.duration_ms, float)  # pyright: ignore[reportAttributeAccessIssue]
    assert success_event.dagster_event.step_success_data.duration_ms > 0.0  # pyright: ignore[reportAttributeAccessIssue]


def test_single_op_job_failure():
    events = defaultdict(list)

    @op
    def op_one():
        raise Exception("nope")

    def _event_callback(record):
        if record.is_dagster_event:
            events[record.dagster_event.event_type].append(record)

    single_op_job = JobDefinition(
        graph_def=GraphDefinition(
            name="single_op_job",
            node_defs=[op_one],
        ),
        logger_defs=get_loggers(_event_callback),
    )

    result = single_op_job.execute_in_process({"loggers": {"callback": {}}}, raise_on_error=False)
    assert not result.success

    start_event = single_dagster_event(events, DagsterEventType.STEP_START)
    assert start_event.job_name == "single_op_job"

    assert start_event.dagster_event.node_name == "op_one"  # pyright: ignore[reportAttributeAccessIssue]
    assert start_event.level == logging.DEBUG  # pyright: ignore[reportAttributeAccessIssue]

    failure_event = single_dagster_event(events, DagsterEventType.STEP_FAILURE)
    assert failure_event.job_name == "single_op_job"

    assert failure_event.dagster_event.node_name == "op_one"  # pyright: ignore[reportAttributeAccessIssue]
    assert failure_event.level == logging.ERROR  # pyright: ignore[reportAttributeAccessIssue]


def define_simple():
    @op
    def yes():
        return "yes"

    @job
    def simple():
        yes()

    return simple


# Generated by printing out an existing serialized event and modifying the event type and
# event_specific_data to types that don't exist yet, to simulate the case where an old
# client deserializes events written from a newer Dagster version
SERIALIZED_EVENT_FROM_THE_FUTURE_WITH_EVENT_SPECIFIC_DATA = (
    '{"__class__": "DagsterEvent", "event_specific_data": {"__class__": "FutureEventData", "foo":'
    ' null, "bar": null, "baz": null, "metadata_entries": [{"__class__": "EventMetadataEntry",'
    ' "description": null, "entry_data": {"__class__": "TextMetadataEntryData", "text": "999"},'
    ' "label": "pid"}]}, "event_type_value": "EVENT_TYPE_FROM_THE_FUTURE", "logging_tags": {},'
    ' "message": "howdy", "pid": null, "pipeline_name": "nonce", "solid_handle": null,'
    ' "step_handle": null, "step_key": "future_step", "step_kind_value": null}'
)

SERIALIZED_EVENT_FROM_THE_FUTURE_WITHOUT_EVENT_SPECIFIC_DATA = (
    '{"__class__": "DagsterEvent", "event_specific_data": null, "event_type_value":'
    ' "EVENT_TYPE_FROM_THE_FUTURE", "logging_tags": {}, "message": "howdy", "pid": null,'
    ' "pipeline_name": "nonce", "solid_handle": null, "step_handle": null, "step_key":'
    ' "future_step", "step_kind_value": null}'
)


def test_event_forward_compat_with_event_specific_data():
    result = deserialize_value(
        SERIALIZED_EVENT_FROM_THE_FUTURE_WITH_EVENT_SPECIFIC_DATA, DagsterEvent
    )

    assert (
        result.message
        == "Could not deserialize event of type EVENT_TYPE_FROM_THE_FUTURE. This event may have"
        ' been written by a newer version of Dagster. Original message: "howdy"'
    )
    assert result.event_type_value == DagsterEventType.ENGINE_EVENT.value
    assert result.job_name == "nonce"
    assert result.step_key == "future_step"
    assert (
        'Attempted to deserialize class "FutureEventData" which is not in the whitelist.'
        in result.event_specific_data.error.message  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    )


def test_event_forward_compat_without_event_specific_data():
    result = deserialize_value(
        SERIALIZED_EVENT_FROM_THE_FUTURE_WITHOUT_EVENT_SPECIFIC_DATA, DagsterEvent
    )

    assert (
        result.message
        == "Could not deserialize event of type EVENT_TYPE_FROM_THE_FUTURE. This event may have"
        ' been written by a newer version of Dagster. Original message: "howdy"'
    )
    assert result.event_type_value == DagsterEventType.ENGINE_EVENT.value
    assert result.job_name == "nonce"
    assert result.step_key == "future_step"
    assert (
        "'EVENT_TYPE_FROM_THE_FUTURE' is not a valid DagsterEventType"
        in result.event_specific_data.error.message  # pyright: ignore[reportOptionalMemberAccess,reportAttributeAccessIssue]
    )


def failing_job_concurrent_events():
    """This job fails, with a specific step consistently failing last."""

    @op(out=DynamicOut())
    def dynamic_op(context):
        for i in range(3):
            yield DynamicOutput(value=i, mapping_key=str(i))

    @op
    def mapped_op(context, i: int):
        time.sleep(i)
        raise Exception("oof")

    @job
    def failing_job():
        dynamic_op().map(mapped_op)

    return failing_job


def test_earliest_step_failure_on_failed_job():
    """Test that the earliest step failure is the one that is logged on the job failure event."""
    with instance_for_test() as instance:
        result = execute_job(
            job=reconstructable(failing_job_concurrent_events),
            instance=instance,
        )
        failure_event = result.get_job_failure_event()
        step_failure = failure_event.job_failure_data.first_step_failure_event
        assert step_failure
        assert step_failure.step_key == "mapped_op[0]"
