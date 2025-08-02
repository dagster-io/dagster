"""Event domain implementation functions - extracted from DagsterInstance."""

import logging
import sys
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Union

import dagster._check as check
from dagster._time import get_current_timestamp

if TYPE_CHECKING:
    from dagster._core.event_api import EventHandlerFn
    from dagster._core.events import (
        DagsterEvent,
        DagsterEventBatchMetadata,
        DagsterEventType,
        EngineEventData,
        JobFailureData,
    )
    from dagster._core.events.log import EventLogEntry
    from dagster._core.instance.events.event_instance_ops import EventInstanceOps
    from dagster._core.storage.dagster_run import DagsterRun
    from dagster._core.storage.event_log.base import (
        EventLogConnection,
        EventLogRecord,
        EventRecordsFilter,
    )


def logs_after(
    ops: "EventInstanceOps",
    run_id: str,
    cursor: Optional[int] = None,
    of_type: Optional["DagsterEventType"] = None,
    limit: Optional[int] = None,
) -> Sequence["EventLogEntry"]:
    """Get logs after cursor - moved from DagsterInstance.logs_after()."""
    return ops.event_storage.get_logs_for_run(
        run_id,
        cursor=cursor,
        of_type=of_type,
        limit=limit,
    )


def all_logs(
    ops: "EventInstanceOps",
    run_id: str,
    of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
) -> Sequence["EventLogEntry"]:
    """Get all logs for run - moved from DagsterInstance.all_logs()."""
    return ops.event_storage.get_logs_for_run(run_id, of_type=of_type)


def get_records_for_run(
    ops: "EventInstanceOps",
    run_id: str,
    cursor: Optional[str] = None,
    of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
    limit: Optional[int] = None,
    ascending: bool = True,
) -> "EventLogConnection":
    """Get event records for run - moved from DagsterInstance.get_records_for_run()."""
    return ops.event_storage.get_records_for_run(run_id, cursor, of_type, limit, ascending)


def watch_event_logs(
    ops: "EventInstanceOps", run_id: str, cursor: Optional[str], cb: "EventHandlerFn"
) -> None:
    """Watch event logs - moved from DagsterInstance.watch_event_logs()."""
    return ops.event_storage.watch(run_id, cursor, cb)


def end_watch_event_logs(ops: "EventInstanceOps", run_id: str, cb: "EventHandlerFn") -> None:
    """End watch event logs - moved from DagsterInstance.end_watch_event_logs()."""
    return ops.event_storage.end_watch(run_id, cb)


def get_event_records(
    ops: "EventInstanceOps",
    event_records_filter: "EventRecordsFilter",
    limit: Optional[int] = None,
    ascending: bool = False,
) -> Sequence["EventLogRecord"]:
    """Return a list of event records stored in the event log storage.
    Moved from DagsterInstance.get_event_records().

    Args:
        event_records_filter (Optional[EventRecordsFilter]): the filter by which to filter event
            records.
        limit (Optional[int]): Number of results to get. Defaults to infinite.
        ascending (Optional[bool]): Sort the result in ascending order if True, descending
            otherwise. Defaults to descending.

    Returns:
        List[EventLogRecord]: List of event log records stored in the event log storage.
    """
    from dagster._core.events import PIPELINE_EVENTS, DagsterEventType

    if (
        event_records_filter.event_type == DagsterEventType.ASSET_MATERIALIZATION_PLANNED
        and event_records_filter.asset_partitions
    ):
        warnings.warn(
            "Asset materialization planned events with partitions subsets will not be "
            "returned when the event records filter contains the asset_partitions argument"
        )
    elif event_records_filter.event_type == DagsterEventType.ASSET_MATERIALIZATION:
        warnings.warn(
            "Use fetch_materializations instead of get_event_records to fetch materialization events."
        )
    elif event_records_filter.event_type == DagsterEventType.ASSET_OBSERVATION:
        warnings.warn(
            "Use fetch_observations instead of get_event_records to fetch observation events."
        )
    elif event_records_filter.event_type in PIPELINE_EVENTS:
        warnings.warn(
            "Use fetch_run_status_changes instead of get_event_records to fetch run status change events."
        )

    return ops.event_storage.get_event_records(event_records_filter, limit, ascending)


def should_store_event(ops: "EventInstanceOps", event: "EventLogEntry") -> bool:
    """Check if event should be stored - moved from DagsterInstance.should_store_event()."""
    if (
        event.dagster_event is not None
        and event.dagster_event.is_asset_failed_to_materialize
        and not ops.event_storage.can_store_asset_failure_events
    ):
        return False
    return True


def store_event(ops: "EventInstanceOps", event: "EventLogEntry") -> None:
    """Store event - moved from DagsterInstance.store_event()."""
    if not should_store_event(ops, event):
        return
    ops.event_storage.store_event(event)


def _is_batch_writing_enabled() -> bool:
    """Check if batch writing is enabled."""
    import os

    return os.getenv("DAGSTER_EVENT_BATCH_WRITING") == "1"


def _get_event_batch_size() -> int:
    """Get event batch size."""
    import os

    return int(os.getenv("DAGSTER_EVENT_BATCH_SIZE", "20"))


def handle_new_event(
    ops: "EventInstanceOps",
    event: "EventLogEntry",
    *,
    batch_metadata: Optional["DagsterEventBatchMetadata"] = None,
) -> None:
    """Handle a new event by storing it and notifying subscribers.
    Moved from DagsterInstance.handle_new_event().

    Events may optionally be sent with `batch_metadata`. If batch writing is enabled, then
    events sent with `batch_metadata` will not trigger an immediate write. Instead, they will be
    kept in a batch-specific buffer (identified by `batch_metadata.id`) until either the buffer
    reaches the event batch size or the end of the batch is reached (signaled by
    `batch_metadata.is_end`). When this point is reached, all events in the buffer will be sent
    to the storage layer in a single batch. If an error occurrs during batch writing, then we
    fall back to iterative individual event writes.

    Args:
        event (EventLogEntry): The event to handle.
        batch_metadata (Optional[DagsterEventBatchMetadata]): Metadata for batch writing.
    """
    from dagster._core.events import RunFailureReason
    from dagster._core.storage.tags import RUN_FAILURE_REASON_TAG, WILL_RETRY_TAG
    from dagster._time import datetime_from_timestamp

    if not should_store_event(ops, event):
        return

    if batch_metadata is None or not _is_batch_writing_enabled():
        events = [event]
    else:
        batch_id, is_batch_end = batch_metadata.id, batch_metadata.is_end
        ops.event_buffer[batch_id].append(event)
        if is_batch_end or len(ops.event_buffer[batch_id]) == _get_event_batch_size():
            events = ops.event_buffer[batch_id]
            del ops.event_buffer[batch_id]
        else:
            return

    if len(events) == 1:
        ops.event_storage.store_event(events[0])
    else:
        try:
            ops.event_storage.store_event_batch(events)

        # Fall back to storing events one by one if writing a batch fails. We catch a generic
        # Exception because that is the parent class of the actually received error,
        # dagster_cloud_cli.core.errors.GraphQLStorageError, which we cannot import here due to
        # it living in a cloud package.
        except Exception as e:
            sys.stderr.write(f"Exception while storing event batch: {e}\n")
            sys.stderr.write("Falling back to storing multiple single-event storage requests...\n")
            for event in events:
                ops.event_storage.store_event(event)

    for event in events:
        run_id = event.run_id
        if (
            not ops.event_storage.handles_run_events_in_store_event
            and event.is_dagster_event
            and event.get_dagster_event().is_job_event
        ):
            ops.run_storage.handle_run_event(
                run_id, event.get_dagster_event(), datetime_from_timestamp(event.timestamp)
            )
            run = ops.get_run_by_id(run_id)
            if run and event.get_dagster_event().is_run_failure and ops.run_retries_enabled:
                # Note that this tag is only applied to runs that fail. Successful runs will not
                # have a WILL_RETRY_TAG tag.
                run_failure_reason = (
                    RunFailureReason(run.tags.get(RUN_FAILURE_REASON_TAG))
                    if run.tags.get(RUN_FAILURE_REASON_TAG)
                    else None
                )
                ops.add_run_tags(
                    run_id,
                    {WILL_RETRY_TAG: str(ops.should_retry_run(run, run_failure_reason)).lower()},
                )
        for sub in ops.subscribers[run_id]:
            sub(event)


def add_event_listener(ops: "EventInstanceOps", run_id: str, cb) -> None:
    """Add event listener - moved from DagsterInstance.add_event_listener()."""
    ops.subscribers[run_id].append(cb)


def report_engine_event(
    ops: "EventInstanceOps",
    message: str,
    dagster_run: Optional["DagsterRun"] = None,
    engine_event_data: Optional["EngineEventData"] = None,
    cls: Optional[type[object]] = None,
    step_key: Optional[str] = None,
    job_name: Optional[str] = None,
    run_id: Optional[str] = None,
) -> "DagsterEvent":
    """Report a EngineEvent that occurred outside of a job execution context.
    Moved from DagsterInstance.report_engine_event().
    """
    from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData
    from dagster._core.storage.dagster_run import DagsterRun

    check.opt_class_param(cls, "cls")
    check.str_param(message, "message")
    check.opt_inst_param(dagster_run, "dagster_run", DagsterRun)
    check.opt_str_param(run_id, "run_id")
    check.opt_str_param(job_name, "job_name")

    check.invariant(
        dagster_run or (job_name and run_id),
        "Must include either dagster_run or job_name and run_id",
    )

    run_id = run_id if run_id else dagster_run.run_id  # type: ignore
    job_name = job_name if job_name else dagster_run.job_name  # type: ignore

    engine_event_data = check.opt_inst_param(
        engine_event_data,
        "engine_event_data",
        EngineEventData,
        EngineEventData({}),
    )

    if cls:
        message = f"[{cls.__name__}] {message}"

    log_level = logging.INFO
    if engine_event_data and engine_event_data.error:
        log_level = logging.ERROR

    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.ENGINE_EVENT.value,
        job_name=job_name,
        message=message,
        event_specific_data=engine_event_data,
        step_key=step_key,
    )
    report_dagster_event(ops, dagster_event, run_id=run_id, log_level=log_level)
    return dagster_event


def report_dagster_event(
    ops: "EventInstanceOps",
    dagster_event: "DagsterEvent",
    run_id: str,
    log_level: Union[str, int] = logging.INFO,
    batch_metadata: Optional["DagsterEventBatchMetadata"] = None,
    timestamp: Optional[float] = None,
) -> None:
    """Takes a DagsterEvent and stores it in persistent storage for the corresponding DagsterRun.
    Moved from DagsterInstance.report_dagster_event().
    """
    from dagster._core.events.log import EventLogEntry

    event_record = EventLogEntry(
        user_message="",
        level=log_level,
        job_name=dagster_event.job_name,
        run_id=run_id,
        error_info=None,
        timestamp=timestamp or get_current_timestamp(),
        step_key=dagster_event.step_key,
        dagster_event=dagster_event,
    )
    handle_new_event(ops, event_record, batch_metadata=batch_metadata)


def report_run_canceling(
    ops: "EventInstanceOps", run: "DagsterRun", message: Optional[str] = None
) -> None:
    """Report run canceling event - moved from DagsterInstance.report_run_canceling()."""
    from dagster._core.events import DagsterEvent, DagsterEventType
    from dagster._core.storage.dagster_run import DagsterRun

    check.inst_param(run, "run", DagsterRun)
    message = check.opt_str_param(
        message,
        "message",
        "Sending run termination request.",
    )
    canceling_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_CANCELING.value,
        job_name=run.job_name,
        message=message,
    )
    report_dagster_event(ops, canceling_event, run_id=run.run_id)


def report_run_canceled(
    ops: "EventInstanceOps",
    dagster_run: "DagsterRun",
    message: Optional[str] = None,
) -> "DagsterEvent":
    """Report run canceled event - moved from DagsterInstance.report_run_canceled()."""
    from dagster._core.events import DagsterEvent, DagsterEventType
    from dagster._core.storage.dagster_run import DagsterRun

    check.inst_param(dagster_run, "dagster_run", DagsterRun)

    message = check.opt_str_param(
        message,
        "mesage",
        "This run has been marked as canceled from outside the execution context.",
    )

    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_CANCELED.value,
        job_name=dagster_run.job_name,
        message=message,
    )
    report_dagster_event(ops, dagster_event, run_id=dagster_run.run_id, log_level=logging.ERROR)
    return dagster_event


def report_run_failed(
    ops: "EventInstanceOps",
    dagster_run: "DagsterRun",
    message: Optional[str] = None,
    job_failure_data: Optional["JobFailureData"] = None,
) -> "DagsterEvent":
    """Report run failed event - moved from DagsterInstance.report_run_failed()."""
    from dagster._core.events import DagsterEvent, DagsterEventType
    from dagster._core.storage.dagster_run import DagsterRun

    check.inst_param(dagster_run, "dagster_run", DagsterRun)

    message = check.opt_str_param(
        message,
        "message",
        "This run has been marked as failed from outside the execution context.",
    )

    dagster_event = DagsterEvent(
        event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
        job_name=dagster_run.job_name,
        message=message,
        event_specific_data=job_failure_data,
    )
    report_dagster_event(ops, dagster_event, run_id=dagster_run.run_id, log_level=logging.ERROR)
    return dagster_event
