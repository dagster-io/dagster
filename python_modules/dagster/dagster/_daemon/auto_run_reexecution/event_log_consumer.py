import os
from typing import Callable, Dict, Iterator, List, Optional

import dagster._check as check
from dagster import DagsterEventType
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import RunRecord, RunsFilter
from dagster._core.workspace.context import IWorkspaceProcessContext

from ..daemon import IntervalDaemon
from .auto_run_reexecution import consume_new_runs_for_automatic_reexecution

_INTERVAL_SECONDS = int(os.environ.get("DAGSTER_EVENT_LOG_CONSUMER_DAEMON_INTERVAL_SECONDS", 5))
_EVENT_LOG_FETCH_LIMIT = int(os.environ.get("DAGSTER_EVENT_LOG_CONSUMER_DAEMON_FETCH_LIMIT", 500))

DAGSTER_EVENT_TYPES = [DagsterEventType.RUN_FAILURE, DagsterEventType.RUN_SUCCESS]


class EventLogConsumerDaemon(IntervalDaemon):
    def __init__(
        self,
        interval_seconds: int = _INTERVAL_SECONDS,
        event_log_fetch_limit: int = _EVENT_LOG_FETCH_LIMIT,
    ):
        super(EventLogConsumerDaemon, self).__init__(interval_seconds=interval_seconds)
        self._event_log_fetch_limit = event_log_fetch_limit

    @classmethod
    def daemon_type(cls) -> str:
        return "EVENT_LOG_CONSUMER"

    @property
    def handle_updated_runs_fns(
        self,
    ) -> List[Callable[[IWorkspaceProcessContext, List[RunRecord]], Iterator]]:
        """
        List of functions that will be called with the list of run records that have new events.
        """
        return [consume_new_runs_for_automatic_reexecution]

    def run_iteration(self, workspace_process_context: IWorkspaceProcessContext):
        instance = workspace_process_context.instance
        # get the persisted cursor for each event type
        persisted_cursors = _fetch_persisted_cursors(instance, DAGSTER_EVENT_TYPES, self._logger)

        # Get the current greatest event id before we query for the specific event types
        overall_max_event_id = instance.event_log_storage.get_maximum_record_id()

        events: List[EventLogEntry] = []
        new_cursors: Dict[
            DagsterEventType, int
        ] = {}  # keep these in memory until we handle the events
        for event_type in DAGSTER_EVENT_TYPES:
            yield

            persisted_cursor = persisted_cursors[event_type]

            events_by_log_id_for_type = instance.event_log_storage.get_logs_for_all_runs_by_log_id(
                after_cursor=persisted_cursor,
                dagster_event_type={event_type},
                limit=self._event_log_fetch_limit,
            )

            events.extend(events_by_log_id_for_type.values())

            # calculate the new cursor for this event type
            new_cursor = get_new_cursor(
                persisted_cursor,
                overall_max_event_id,
                self._event_log_fetch_limit,
                list(events_by_log_id_for_type.keys()),
            )
            if new_cursor is not None:
                new_cursors[event_type] = new_cursor

        if events:
            run_ids = list({event.run_id for event in events})
            run_records = instance.get_run_records(filters=RunsFilter(run_ids=run_ids))

            # call each handler with the list of runs that have events
            for fn in self.handle_updated_runs_fns:
                try:
                    yield from fn(workspace_process_context, run_records)
                except Exception:
                    self._logger.exception(
                        "Error calling event event log consumer handler: {handler_fn}".format(
                            handler_fn=fn.__name__,
                        )
                    )

        # persist cursors now that we've processed all the events through the handlers
        _persist_cursors(instance, new_cursors)


def _create_cursor_key(event_type: DagsterEventType):
    check.inst_param(event_type, "event_type", DagsterEventType)

    return f"EVENT_LOG_CONSUMER_CURSOR-{event_type.value}"


def _fetch_persisted_cursors(
    instance: DagsterInstance, event_types: List[DagsterEventType], logger
) -> Dict[DagsterEventType, int]:
    check.inst_param(instance, "instance", DagsterInstance)
    check.list_param(event_types, "event_types", of_type=DagsterEventType)

    # get the persisted cursor for each event type
    persisted_cursors = instance.run_storage.kvs_get(
        {_create_cursor_key(event_type) for event_type in event_types}
    )

    fetched_cursors = {}
    for event_type in event_types:
        raw_cursor_value = persisted_cursors.get(_create_cursor_key(event_type))
        if raw_cursor_value is None:
            logger.warn(
                "No cursor for event type {}, starting from the beginning".format(event_type)
            )
            raw_cursor_value = "0"

        try:
            cursor_value = int(raw_cursor_value)
        except ValueError:
            # if this cursor got corrupted somehow, reset it to 0
            logger.exception(
                "Invalid cursor for event_type {}: {}".format(event_type, raw_cursor_value)
            )
            raise

        fetched_cursors[event_type] = cursor_value

    return fetched_cursors


def _persist_cursors(instance: DagsterInstance, cursors: Dict[DagsterEventType, int]) -> None:
    check.inst_param(instance, "instance", DagsterInstance)
    check.dict_param(cursors, "cursors", key_type=DagsterEventType, value_type=int)

    if cursors:
        instance.run_storage.kvs_set(
            {
                _create_cursor_key(event_type): str(cursor_value)
                for event_type, cursor_value in cursors.items()
            }
        )


def get_new_cursor(
    persisted_cursor: int,
    overall_max_event_id: Optional[int],
    fetch_limit: int,
    new_event_ids: List[int],
) -> Optional[int]:
    """
    Return the new cursor value for an event type, or None if one shouldn't be persisted. The cursor
    is guaranteed to be:

    - greater than or equal to any id in new_event_ids (otherwise we could process an event twice)
    - less than the id of any event of the desired type that hasn't been fetched yet (otherwise we
      could skip events)

    This method optimizes for moving the cursor as far forward as possible, using
    overall_max_event_id.
    """

    check.int_param(persisted_cursor, "persisted_cursor")
    check.opt_int_param(overall_max_event_id, "overall_max_event_id")
    check.int_param(fetch_limit, "fetch_limit")
    check.list_param(new_event_ids, "new_event_ids", of_type=int)

    if overall_max_event_id is None:
        # We only get here if the event log was empty when we queried it for the overall max.
        if new_event_ids:
            # We only get here if some events snuck in after the max id query. Set the cursor
            # to the max event id of the new events.
            return max(new_event_ids)

        # Event log is empty, don't bother setting a cursor.
        return None

    if not new_event_ids:
        # No new events, so we can skip to overall_max_event_id because we queried that first, so we
        # know there are no relevant events up to that id.
        return overall_max_event_id

    # these should be ordered, but we won't assume
    max_new_event_id = max(new_event_ids)

    check.invariant(
        max_new_event_id > persisted_cursor,
        "The new cursor {} should be greater than the previous {}".format(
            max_new_event_id, persisted_cursor
        ),
    )

    num_new_events = len(new_event_ids)
    check.invariant(
        num_new_events <= fetch_limit,
        "Query returned more than the limit!",
    )

    if num_new_events == fetch_limit:
        # We got back the limit number of events, so the only thing we can do is move the cursor
        # forward to the max event id of the new events. It's possible for the very next log id
        # to be the desired type. There's no way to skip ahead.
        return max_new_event_id
    else:
        # We got back fewer than the limit number of events, so we may be able to skip ahead. Since
        # we queried for overall_max_event_id before we queried for events of the desired type, we
        # know that there can be no events of the desired type with ids less than overall_max_event_id
        # that we haven't fetched yet (they would have been in this query, up until it reached the
        # fetch limit). Thus we can skip ahead to overall_max_event_id.
        if overall_max_event_id >= max_new_event_id:
            return overall_max_event_id

        # There's also a rare case where more events of our desired type snuck in after the query
        # for overall_max_event_id but before the specific event query. In this case, we just move
        # the cursor forward to the max event id of the new events.
        return max_new_event_id
