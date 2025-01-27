import time
from collections.abc import Mapping
from typing import Optional

from dagster import DagsterInstance, DagsterRun, DagsterRunStatus, RunsFilter


def poll_for_finished_run(
    instance: DagsterInstance,
    run_id: Optional[str] = None,
    timeout: float = 20,
    run_tags: Optional[Mapping[str, str]] = None,
) -> DagsterRun:
    total_time = 0
    interval = 0.01

    filters = RunsFilter(
        run_ids=[run_id] if run_id else None,
        tags=run_tags,
        statuses=[
            DagsterRunStatus.SUCCESS,
            DagsterRunStatus.FAILURE,
            DagsterRunStatus.CANCELED,
        ],
    )

    while True:
        runs = instance.get_runs(filters, limit=1)
        if runs:
            return runs[0]
        else:
            time.sleep(interval)
            total_time += interval
            if total_time > timeout:
                raise Exception("Timed out")


def poll_for_step_start(instance: DagsterInstance, run_id: str, timeout: float = 30):
    poll_for_event(instance, run_id, event_type="STEP_START", message=None, timeout=timeout)


def poll_for_event(
    instance: DagsterInstance,
    run_id: str,
    event_type: str,
    message: Optional[str],
    timeout: float = 30,
) -> None:
    total_time = 0
    backoff = 0.01

    while True:
        time.sleep(backoff)
        logs = instance.all_logs(run_id)
        matching_events = [
            log_record.get_dagster_event()
            for log_record in logs
            if log_record.is_dagster_event
            and log_record.get_dagster_event().event_type_value == event_type
        ]
        if matching_events:
            if message is None:
                return
            for matching_message in (event.message for event in matching_events):
                if matching_message and message in matching_message:
                    return

        total_time += backoff
        backoff = backoff * 2
        if total_time > timeout:
            raise Exception("Timed out")
