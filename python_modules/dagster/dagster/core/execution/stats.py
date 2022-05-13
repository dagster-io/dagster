from collections import defaultdict
from enum import Enum
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, cast

import dagster._check as check
from dagster.core.definitions import ExpectationResult
from dagster.core.events import DagsterEventType, StepExpectationResultData
from dagster.core.events.log import EventLogEntry
from dagster.core.storage.pipeline_run import PipelineRunStatsSnapshot
from dagster.serdes import whitelist_for_serdes
from dagster.utils import datetime_as_float


def build_run_stats_from_events(run_id, records):
    try:
        iter(records)
    except TypeError as exc:
        raise check.ParameterCheckError(
            "Invariant violation for parameter 'records'. Description: Expected iterable."
        ) from exc
    for i, record in enumerate(records):
        check.inst_param(record, f"records[{i}]", EventLogEntry)

    steps_succeeded = 0
    steps_failed = 0
    materializations = 0
    expectations = 0
    enqueued_time = None
    launch_time = None
    start_time = None
    end_time = None

    for event in records:
        if not event.is_dagster_event:
            continue
        dagster_event = event.get_dagster_event()

        event_timestamp_float = (
            event.timestamp
            if isinstance(event.timestamp, float)
            else datetime_as_float(event.timestamp)
        )
        if dagster_event.event_type == DagsterEventType.PIPELINE_START:
            start_time = event_timestamp_float
        if dagster_event.event_type == DagsterEventType.PIPELINE_STARTING:
            launch_time = event_timestamp_float
        if dagster_event.event_type == DagsterEventType.PIPELINE_ENQUEUED:
            enqueued_time = event_timestamp_float
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
            end_time = (
                event.timestamp
                if isinstance(event.timestamp, float)
                else datetime_as_float(event.timestamp)
            )

    return PipelineRunStatsSnapshot(
        run_id,
        steps_succeeded,
        steps_failed,
        materializations,
        expectations,
        enqueued_time,
        launch_time,
        start_time,
        end_time,
    )


class StepEventStatus(Enum):
    SKIPPED = "SKIPPED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    IN_PROGRESS = "IN_PROGRESS"


def build_run_step_stats_from_events(
    run_id: str, records: Iterable[EventLogEntry]
) -> List["RunStepKeyStatsSnapshot"]:
    by_step_key: Dict[str, Dict[str, Any]] = defaultdict(dict)
    attempts = defaultdict(list)
    attempt_events = defaultdict(list)
    markers: Dict[str, Dict[str, Any]] = defaultdict(dict)
    for event in records:
        if not event.is_dagster_event:
            continue
        dagster_event = event.get_dagster_event()

        step_key = dagster_event.step_key
        if not step_key:
            continue

        if dagster_event.event_type == DagsterEventType.STEP_START:
            by_step_key[step_key]["start_time"] = event.timestamp
            by_step_key[step_key]["attempts"] = 1
        if dagster_event.event_type == DagsterEventType.STEP_FAILURE:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.FAILURE
        if dagster_event.event_type == DagsterEventType.STEP_RESTARTED:
            by_step_key[step_key]["attempts"] = int(by_step_key[step_key].get("attempts") or 0) + 1
        if dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.SUCCESS
        if dagster_event.event_type == DagsterEventType.STEP_SKIPPED:
            by_step_key[step_key]["end_time"] = event.timestamp
            by_step_key[step_key]["status"] = StepEventStatus.SKIPPED
        if dagster_event.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            materialization_events = by_step_key[step_key].get("materialization_events", [])
            materialization_events.append(event)
            by_step_key[step_key]["materialization_events"] = materialization_events
        if dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
            expectation_data = cast(StepExpectationResultData, dagster_event.event_specific_data)
            expectation_result = expectation_data.expectation_result
            step_expectation_results = by_step_key[step_key].get("expectation_results", [])
            step_expectation_results.append(expectation_result)
            by_step_key[step_key]["expectation_results"] = step_expectation_results
        if dagster_event.event_type in (
            DagsterEventType.STEP_UP_FOR_RETRY,
            DagsterEventType.STEP_RESTARTED,
        ):
            attempt_events[step_key].append(event)
        if dagster_event.event_type == DagsterEventType.ENGINE_EVENT:
            if dagster_event.engine_event_data.marker_start:
                key = dagster_event.engine_event_data.marker_start
                if key not in markers[step_key]:
                    markers[step_key][key] = {"key": key, "start": event.timestamp}
                else:
                    markers[step_key][key]["start"] = event.timestamp

            if dagster_event.engine_event_data.marker_end:
                key = dagster_event.engine_event_data.marker_end
                if key not in markers[step_key]:
                    markers[step_key][key] = {"key": key, "end": event.timestamp}
                else:
                    markers[step_key][key]["end"] = event.timestamp

    for step_key, step_stats in by_step_key.items():
        events = attempt_events[step_key]
        step_attempts = []
        attempt_start = step_stats.get("start_time")

        for event in events:
            if not event.dagster_event:
                continue
            if event.dagster_event.event_type == DagsterEventType.STEP_UP_FOR_RETRY:
                step_attempts.append(
                    RunStepMarker(start_time=attempt_start, end_time=event.timestamp)
                )
            elif event.dagster_event.event_type == DagsterEventType.STEP_RESTARTED:
                attempt_start = event.timestamp
        if step_stats.get("end_time"):
            step_attempts.append(
                RunStepMarker(start_time=attempt_start, end_time=step_stats["end_time"])
            )
        else:
            by_step_key[step_key]["status"] = StepEventStatus.IN_PROGRESS
        attempts[step_key] = step_attempts

    return [
        RunStepKeyStatsSnapshot(
            run_id=run_id,
            step_key=step_key,
            attempts_list=attempts[step_key],
            markers=[
                RunStepMarker(start_time=marker.get("start"), end_time=marker.get("end"))
                for marker in markers[step_key].values()
            ],
            **value,
        )
        for step_key, value in by_step_key.items()
    ]


@whitelist_for_serdes
class RunStepMarker(
    NamedTuple(
        "_RunStepMarker",
        [("start_time", Optional[float]), ("end_time", Optional[float])],
    )
):
    def __new__(
        cls,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ):
        return super(RunStepMarker, cls).__new__(
            cls,
            start_time=check.opt_float_param(start_time, "start_time"),
            end_time=check.opt_float_param(end_time, "end_time"),
        )


@whitelist_for_serdes
class RunStepKeyStatsSnapshot(
    NamedTuple(
        "_RunStepKeyStatsSnapshot",
        [
            ("run_id", str),
            ("step_key", str),
            ("status", Optional[StepEventStatus]),
            ("start_time", Optional[float]),
            ("end_time", Optional[float]),
            ("materialization_events", List[EventLogEntry]),
            ("expectation_results", List[ExpectationResult]),
            ("attempts", Optional[int]),
            ("attempts_list", List[RunStepMarker]),
            ("markers", List[RunStepMarker]),
        ],
    )
):
    def __new__(
        cls,
        run_id: str,
        step_key: str,
        status: Optional[StepEventStatus] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        materialization_events: Optional[List[EventLogEntry]] = None,
        expectation_results: Optional[List[ExpectationResult]] = None,
        attempts: Optional[int] = None,
        attempts_list: Optional[List[RunStepMarker]] = None,
        markers: Optional[List[RunStepMarker]] = None,
    ):
        return super(RunStepKeyStatsSnapshot, cls).__new__(
            cls,
            run_id=check.str_param(run_id, "run_id"),
            step_key=check.str_param(step_key, "step_key"),
            status=check.opt_inst_param(status, "status", StepEventStatus),
            start_time=check.opt_float_param(start_time, "start_time"),
            end_time=check.opt_float_param(end_time, "end_time"),
            materialization_events=check.opt_list_param(
                materialization_events,
                "materialization_events",
                EventLogEntry,
            ),
            expectation_results=check.opt_list_param(
                expectation_results, "expectation_results", ExpectationResult
            ),
            attempts=check.opt_int_param(attempts, "attempts"),
            attempts_list=check.opt_list_param(attempts_list, "attempts_list", RunStepMarker),
            markers=check.opt_list_param(markers, "markers", RunStepMarker),
        )
