from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from typing import Any, Optional, cast

import dagster._check as check
from dagster._core.definitions import ExpectationResult
from dagster._core.events import (
    MARKER_EVENTS,
    PIPELINE_EVENTS,
    DagsterEventType,
    StepExpectationResultData,
)
from dagster._core.events.log import EventLogEntry
from dagster._core.storage.dagster_run import DagsterRunStatsSnapshot
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import whitelist_for_serdes

RUN_STATS_EVENT_TYPES = {
    *PIPELINE_EVENTS,
    DagsterEventType.STEP_FAILURE,
    DagsterEventType.STEP_SUCCESS,
    DagsterEventType.ASSET_MATERIALIZATION,
    DagsterEventType.STEP_EXPECTATION_RESULT,
}

STEP_STATS_EVENT_TYPES = {
    DagsterEventType.STEP_START,
    DagsterEventType.STEP_FAILURE,
    DagsterEventType.STEP_RESTARTED,
    DagsterEventType.STEP_SUCCESS,
    DagsterEventType.STEP_SKIPPED,
    DagsterEventType.ASSET_MATERIALIZATION,
    DagsterEventType.STEP_EXPECTATION_RESULT,
    DagsterEventType.STEP_UP_FOR_RETRY,
    DagsterEventType.STEP_RESTARTED,
    *MARKER_EVENTS,
}


def build_run_stats_from_events(
    run_id: str,
    entries: Iterable[EventLogEntry],
    previous_stats: Optional[DagsterRunStatsSnapshot] = None,
) -> DagsterRunStatsSnapshot:
    try:
        iter(entries)
    except TypeError as exc:
        raise check.ParameterCheckError(
            "Invariant violation for parameter 'records'. Description: Expected iterable."
        ) from exc
    for i, entry in enumerate(entries):
        check.inst_param(entry, f"entries[{i}]", EventLogEntry)

    if previous_stats:
        steps_succeeded = previous_stats.steps_succeeded
        steps_failed = previous_stats.steps_failed
        materializations = previous_stats.materializations
        expectations = previous_stats.expectations
        enqueued_time = previous_stats.enqueued_time
        launch_time = previous_stats.launch_time
        start_time = previous_stats.start_time
        end_time = previous_stats.end_time
    else:
        steps_succeeded = 0
        steps_failed = 0
        materializations = 0
        expectations = 0
        enqueued_time = None
        launch_time = None
        start_time = None
        end_time = None

    for event in entries:
        if not event.is_dagster_event:
            continue
        dagster_event = event.get_dagster_event()

        if dagster_event.event_type == DagsterEventType.PIPELINE_START:
            start_time = event.timestamp
        if dagster_event.event_type == DagsterEventType.PIPELINE_STARTING:
            launch_time = event.timestamp
        if dagster_event.event_type == DagsterEventType.PIPELINE_ENQUEUED:
            enqueued_time = event.timestamp
        if dagster_event.event_type == DagsterEventType.STEP_FAILURE:
            steps_failed += 1
        if dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
            steps_succeeded += 1
        if dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            materializations += 1
        if dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
            expectations += 1
        if (
            dagster_event.event_type == DagsterEventType.PIPELINE_SUCCESS
            or dagster_event.event_type == DagsterEventType.PIPELINE_FAILURE
            or dagster_event.event_type == DagsterEventType.PIPELINE_CANCELED
        ):
            end_time = event.timestamp

    return DagsterRunStatsSnapshot(
        run_id=run_id,
        steps_succeeded=steps_succeeded,
        steps_failed=steps_failed,
        materializations=materializations,
        expectations=expectations,
        enqueued_time=enqueued_time,
        launch_time=launch_time,
        start_time=start_time,
        end_time=end_time,
    )


@whitelist_for_serdes
class StepEventStatus(Enum):
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    IN_PROGRESS = "IN_PROGRESS"


@whitelist_for_serdes
@record_custom
class RunStepMarker(IHaveNew):
    start_time: Optional[float]
    end_time: Optional[float]
    key: Optional[str]

    def __new__(
        cls,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        key: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            start_time=check.opt_float_param(start_time, "start_time"),
            end_time=check.opt_float_param(end_time, "end_time"),
            key=check.opt_str_param(key, "key"),
        )


@whitelist_for_serdes
@record_custom
class RunStepKeyStatsSnapshot(IHaveNew):
    run_id: str
    step_key: str
    status: Optional[StepEventStatus]
    start_time: Optional[float]
    end_time: Optional[float]
    materialization_events: Sequence[EventLogEntry]
    expectation_results: Sequence[ExpectationResult]
    attempts: Optional[int]
    attempts_list: Sequence[RunStepMarker]
    markers: Sequence[RunStepMarker]
    partial_attempt_start: Optional[float]

    def __new__(
        cls,
        run_id: str,
        step_key: str,
        status: Optional[StepEventStatus] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        materialization_events: Optional[Sequence[EventLogEntry]] = None,
        expectation_results: Optional[Sequence[ExpectationResult]] = None,
        attempts: Optional[int] = None,
        attempts_list: Optional[Sequence[RunStepMarker]] = None,
        markers: Optional[Sequence[RunStepMarker]] = None,
        partial_attempt_start: Optional[float] = None,
    ):
        return super().__new__(
            cls,
            run_id=check.str_param(run_id, "run_id"),
            step_key=check.str_param(step_key, "step_key"),
            status=check.opt_inst_param(status, "status", StepEventStatus),
            start_time=check.opt_float_param(start_time, "start_time"),
            end_time=check.opt_float_param(end_time, "end_time"),
            materialization_events=check.opt_sequence_param(
                materialization_events,
                "materialization_events",
                EventLogEntry,
            ),
            expectation_results=check.opt_sequence_param(
                expectation_results, "expectation_results", ExpectationResult
            ),
            attempts=check.opt_int_param(attempts, "attempts"),
            attempts_list=check.opt_sequence_param(attempts_list, "attempts_list", RunStepMarker),
            markers=check.opt_sequence_param(markers, "markers", RunStepMarker),
            # used to calculate incremental step stats using batches of event logs
            partial_attempt_start=check.opt_float_param(
                partial_attempt_start, "partial_attempt_start"
            ),
        )


@whitelist_for_serdes
@record
class RunStepStatsSnapshot:
    run_id: str
    step_key_stats: Sequence[RunStepKeyStatsSnapshot]
    partial_markers: Optional[Mapping[str, Sequence[RunStepMarker]]]


def build_run_step_stats_from_events(
    run_id: str,
    entries: Iterable[EventLogEntry],
) -> Sequence[RunStepKeyStatsSnapshot]:
    snapshot = build_run_step_stats_snapshot_from_events(run_id, entries)
    return snapshot.step_key_stats


def build_run_step_stats_snapshot_from_events(
    run_id: str,
    entries: Iterable[EventLogEntry],
    previous_snapshot: Optional["RunStepStatsSnapshot"] = None,
) -> "RunStepStatsSnapshot":
    by_step_key: dict[str, dict[str, Any]] = defaultdict(dict)
    attempts = defaultdict(list)
    markers: dict[str, dict[str, Any]] = defaultdict(dict)

    if previous_snapshot:
        for step_stats in previous_snapshot.step_key_stats:
            check.invariant(step_stats.run_id == run_id)
            by_step_key[step_stats.step_key] = {
                "start_time": step_stats.start_time,
                "end_time": step_stats.end_time,
                "status": step_stats.status,
                "materialization_events": step_stats.materialization_events,
                "expectation_results": step_stats.expectation_results,
                "attempts": step_stats.attempts,
                "partial_attempt_start": step_stats.partial_attempt_start,
            }
            for attempt in step_stats.attempts_list:
                attempts[step_stats.step_key].append(attempt)

            for marker in step_stats.markers:
                assert marker.key
                markers[step_stats.step_key][marker.key] = {
                    "key": marker.key,
                    "start": marker.start_time,
                    "end": marker.end_time,
                }

        # handle the partial markers
        if previous_snapshot.partial_markers:
            for step_key, partial_markers in previous_snapshot.partial_markers.items():
                for marker in partial_markers:
                    assert marker.key
                    markers[step_key][marker.key] = {
                        "key": marker.key,
                        "start": marker.start_time,
                        "end": marker.end_time,
                    }

    def _open_attempt(step_key: str, event: EventLogEntry) -> None:
        by_step_key[step_key]["attempts"] = int(by_step_key[step_key].get("attempts") or 0) + 1
        by_step_key[step_key]["partial_attempt_start"] = event.timestamp

    def _close_attempt(step_key: str, event: EventLogEntry) -> None:
        start_time = by_step_key[step_key].get("partial_attempt_start")

        if start_time is None:
            # this should only happen if the step was retried before starting (weird)
            by_step_key[step_key]["attempts"] = int(by_step_key[step_key].get("attempts") or 0) + 1
            start_time = event.timestamp

        attempts[step_key].append(
            RunStepMarker(
                start_time=start_time,
                end_time=event.timestamp,
            )
        )
        by_step_key[step_key]["partial_attempt_start"] = None

    for event in entries:
        if not event.is_dagster_event:
            continue
        dagster_event = event.get_dagster_event()

        step_key = dagster_event.step_key
        if not step_key:
            continue

        if dagster_event.event_type not in STEP_STATS_EVENT_TYPES:
            continue

        if dagster_event.event_type == DagsterEventType.STEP_START:
            by_step_key[step_key]["status"] = StepEventStatus.IN_PROGRESS
            by_step_key[step_key]["start_time"] = event.timestamp
            _open_attempt(step_key, event)
        if dagster_event.event_type == DagsterEventType.STEP_RESTARTED:
            _open_attempt(step_key, event)
        if dagster_event.event_type == DagsterEventType.STEP_UP_FOR_RETRY:
            _close_attempt(step_key, event)
        if dagster_event.event_type == DagsterEventType.STEP_FAILURE:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.FAILURE
            _close_attempt(step_key, event)
        if dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.SUCCESS
            _close_attempt(step_key, event)
        if dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.SKIPPED
            _close_attempt(step_key, event)
        if dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            materialization_events = by_step_key[step_key].get("materialization_events", [])
            materialization_events.append(event)
            by_step_key[step_key]["materialization_events"] = materialization_events
        if dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
            expectation_data = cast("StepExpectationResultData", dagster_event.event_specific_data)
            expectation_result = expectation_data.expectation_result
            step_expectation_results = by_step_key[step_key].get("expectation_results", [])
            step_expectation_results.append(expectation_result)
            by_step_key[step_key]["expectation_results"] = step_expectation_results

        if dagster_event.event_type in MARKER_EVENTS:
            if dagster_event.engine_event_data.marker_start:
                marker_key = dagster_event.engine_event_data.marker_start
                if marker_key not in markers[step_key]:
                    markers[step_key][marker_key] = {"key": marker_key, "start": event.timestamp}
                else:
                    markers[step_key][marker_key]["start"] = event.timestamp

            if dagster_event.engine_event_data.marker_end:
                marker_key = dagster_event.engine_event_data.marker_end
                if marker_key not in markers[step_key]:
                    markers[step_key][marker_key] = {"key": marker_key, "end": event.timestamp}
                else:
                    markers[step_key][marker_key]["end"] = event.timestamp

    snapshots = []
    for step_key, step_stats in by_step_key.items():
        snapshots.append(
            RunStepKeyStatsSnapshot(
                run_id=run_id,
                step_key=step_key,
                **step_stats,
                markers=[
                    RunStepMarker(
                        start_time=marker.get("start"),
                        end_time=marker.get("end"),
                        key=marker.get("key"),
                    )
                    for marker in markers[step_key].values()
                ],
                attempts_list=attempts[step_key],
            )
        )

    return RunStepStatsSnapshot(
        run_id=run_id,
        step_key_stats=snapshots,
        partial_markers={
            step_key: [
                RunStepMarker(start_time=marker.get("start"), end_time=marker.get("end"), key=key)
                for key, marker in markers.items()
            ]
            for step_key, markers in markers.items()
            if step_key not in by_step_key
        },
    )
