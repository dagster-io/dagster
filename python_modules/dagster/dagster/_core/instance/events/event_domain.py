"""Event domain implementation - extracted from DagsterInstance."""

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
    from dagster._core.instance import DagsterInstance
    from dagster._core.storage.dagster_run import DagsterRun
    from dagster._core.storage.event_log.base import (
        EventLogConnection,
        EventLogRecord,
        EventRecordsFilter,
    )


class EventDomain:
    """Domain object encapsulating event-related operations.

    This class holds a reference to a DagsterInstance and provides methods
    for event storage, querying, and streaming.
    """

    def __init__(self, instance: "DagsterInstance") -> None:
        self._instance = instance

    def logs_after(
        self,
        run_id: str,
        cursor: Optional[int] = None,
        of_type: Optional["DagsterEventType"] = None,
        limit: Optional[int] = None,
    ) -> Sequence["EventLogEntry"]:
        """Get logs after cursor - moved from DagsterInstance.logs_after()."""
        return self._instance._event_storage.get_logs_for_run(  # noqa: SLF001
            run_id,
            cursor=cursor,
            of_type=of_type,
            limit=limit,
        )

    def all_logs(
        self,
        run_id: str,
        of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
    ) -> Sequence["EventLogEntry"]:
        """Get all logs for run - moved from DagsterInstance.all_logs()."""
        return self._instance._event_storage.get_logs_for_run(run_id, of_type=of_type)  # noqa: SLF001

    def get_records_for_run(
        self,
        run_id: str,
        cursor: Optional[str] = None,
        of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> "EventLogConnection":
        """Get event records for run - moved from DagsterInstance.get_records_for_run()."""
        return self._instance._event_storage.get_records_for_run(  # noqa: SLF001
            run_id, cursor, of_type, limit, ascending
        )

    def watch_event_logs(self, run_id: str, cursor: Optional[str], cb: "EventHandlerFn") -> None:
        """Watch event logs - moved from DagsterInstance.watch_event_logs()."""
        return self._instance._event_storage.watch(run_id, cursor, cb)  # noqa: SLF001

    def end_watch_event_logs(self, run_id: str, cb: "EventHandlerFn") -> None:
        """End watch event logs - moved from DagsterInstance.end_watch_event_logs()."""
        return self._instance._event_storage.end_watch(run_id, cb)  # noqa: SLF001

    def get_event_records(
        self,
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

        return self._instance._event_storage.get_event_records(  # noqa: SLF001
            event_records_filter, limit, ascending
        )

    def should_store_event(self, event: "EventLogEntry") -> bool:
        """Check if event should be stored - moved from DagsterInstance.should_store_event()."""
        if (
            event.dagster_event is not None
            and event.dagster_event.is_asset_failed_to_materialize
            and not self._instance._event_storage.can_store_asset_failure_events  # noqa: SLF001
        ):
            return False
        return True

    def store_event(self, event: "EventLogEntry") -> None:
        """Store event - moved from DagsterInstance.store_event()."""
        if not self.should_store_event(event):
            return
        self._instance._event_storage.store_event(event)  # noqa: SLF001

    def _is_batch_writing_enabled(self) -> bool:
        """Check if batch writing is enabled."""
        return self._get_event_batch_size() > 0

    def _get_event_batch_size(self) -> int:
        """Get event batch size."""
        import os

        return int(os.getenv("DAGSTER_EVENT_BATCH_SIZE", "0"))

    def handle_new_event(
        self,
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

        if not self.should_store_event(event):
            return

        if batch_metadata is None or not self._is_batch_writing_enabled():
            events = [event]
        else:
            batch_id, is_batch_end = batch_metadata.id, batch_metadata.is_end
            self._instance._event_buffer[batch_id].append(event)  # noqa: SLF001
            if (
                is_batch_end
                or len(self._instance._event_buffer[batch_id]) == self._get_event_batch_size()  # noqa: SLF001
            ):
                events = self._instance._event_buffer[batch_id]  # noqa: SLF001
                del self._instance._event_buffer[batch_id]  # noqa: SLF001
            else:
                return

        if len(events) == 1:
            self._instance._event_storage.store_event(events[0])  # noqa: SLF001
        else:
            try:
                self._instance._event_storage.store_event_batch(events)  # noqa: SLF001

            # Fall back to storing events one by one if writing a batch fails. We catch a generic
            # Exception because that is the parent class of the actually received error,
            # dagster_cloud_cli.core.errors.GraphQLStorageError, which we cannot import here due to
            # it living in a cloud package.
            except Exception as e:
                sys.stderr.write(f"Exception while storing event batch: {e}\n")
                sys.stderr.write(
                    "Falling back to storing multiple single-event storage requests...\n"
                )
                for event in events:
                    self._instance._event_storage.store_event(event)  # noqa: SLF001

        for event in events:
            run_id = event.run_id
            if (
                not self._instance._event_storage.handles_run_events_in_store_event  # noqa: SLF001
                and event.is_dagster_event
                and event.get_dagster_event().is_job_event
            ):
                self._instance._run_storage.handle_run_event(  # noqa: SLF001
                    run_id, event.get_dagster_event(), datetime_from_timestamp(event.timestamp)
                )
                run = self._instance.get_run_by_id(run_id)
                if (
                    run
                    and event.get_dagster_event().is_run_failure
                    and self._instance.run_retries_enabled
                ):
                    # Note that this tag is only applied to runs that fail. Successful runs will not
                    # have a WILL_RETRY_TAG tag.
                    run_failure_reason = (
                        RunFailureReason(run.tags.get(RUN_FAILURE_REASON_TAG))
                        if run.tags.get(RUN_FAILURE_REASON_TAG)
                        else None
                    )
                    self._instance.add_run_tags(
                        run_id,
                        {
                            WILL_RETRY_TAG: str(
                                self._should_retry_run(run, run_failure_reason)
                            ).lower()
                        },
                    )
            for sub in self._instance._subscribers[run_id]:  # noqa: SLF001
                sub(event)

    def _should_retry_run(self, run, run_failure_reason):
        """Helper method to check if run should be retried."""
        from dagster._daemon.auto_run_reexecution.auto_run_reexecution import (
            auto_reexecution_should_retry_run,
        )

        return auto_reexecution_should_retry_run(self._instance, run, run_failure_reason)

    def add_event_listener(self, run_id: str, cb) -> None:
        """Add event listener - moved from DagsterInstance.add_event_listener()."""
        self._instance._subscribers[run_id].append(cb)  # noqa: SLF001

    def report_engine_event(
        self,
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
        self.report_dagster_event(dagster_event, run_id=run_id, log_level=log_level)
        return dagster_event

    def report_dagster_event(
        self,
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
        self.handle_new_event(event_record, batch_metadata=batch_metadata)

    def report_run_canceling(self, run: "DagsterRun", message: Optional[str] = None) -> None:
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
        self.report_dagster_event(canceling_event, run_id=run.run_id)

    def report_run_canceled(
        self,
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
        self.report_dagster_event(dagster_event, run_id=dagster_run.run_id, log_level=logging.ERROR)
        return dagster_event

    def report_run_failed(
        self,
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
        self.report_dagster_event(dagster_event, run_id=dagster_run.run_id, log_level=logging.ERROR)
        return dagster_event
