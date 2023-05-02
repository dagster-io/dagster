from typing import Any

from dagster._core.host_representation.external import ExternalJob
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.test_utils import create_run_for_test, poll_for_finished_run
from dagster._utils import file_relative_path
from dagster._utils.merger import merge_dicts
from utils import start_daemon


def create_run(instance: DagsterInstance, external_job: ExternalJob, **kwargs: Any) -> DagsterRun:
    job_args = merge_dicts(
        {
            "job_name": "foo_job",
            "external_job_origin": external_job.get_external_origin(),
            "job_code_origin": external_job.get_python_origin(),
        },
        kwargs,
    )
    return create_run_for_test(instance, **job_args)


def assert_events_in_order(logs, expected_events):
    logged_events = [log.dagster_event.event_type_value for log in logs if log.is_dagster_event]
    filtered_logged_events = [event for event in logged_events if event in expected_events]

    assert filtered_logged_events == expected_events


def test_queue_from_schedule_and_sensor(instance, foo_example_workspace, foo_example_repo):
    external_schedule = foo_example_repo.get_external_schedule("always_run_schedule")
    external_sensor = foo_example_repo.get_external_sensor("always_on_sensor")
    external_job = foo_example_repo.get_full_external_job("foo_job")

    instance.start_schedule(external_schedule)
    instance.start_sensor(external_sensor)

    with start_daemon(timeout=180, workspace_file=file_relative_path(__file__, "repo.py")):
        run = create_run(instance, external_job)
        instance.submit_run(run.run_id, foo_example_workspace)

        runs = [
            poll_for_finished_run(instance, run.run_id),
            poll_for_finished_run(instance, run_tags=DagsterRun.tags_for_sensor(external_sensor)),
            poll_for_finished_run(
                instance,
                run_tags=DagsterRun.tags_for_schedule(external_schedule),
                timeout=90,
            ),
        ]

        for run in runs:
            logs = instance.all_logs(run.run_id)
            assert_events_in_order(
                logs,
                [
                    "PIPELINE_ENQUEUED",
                    "PIPELINE_STARTING",
                    "PIPELINE_START",
                    "PIPELINE_SUCCESS",
                ],
            )


def test_queued_runs(instance, foo_example_workspace, foo_example_repo):
    with start_daemon(workspace_file=file_relative_path(__file__, "repo.py")):
        external_job = foo_example_repo.get_full_external_job("foo_job")

        run = create_run(instance, external_job)

        instance.submit_run(run.run_id, foo_example_workspace)

        poll_for_finished_run(instance, run.run_id)

        logs = instance.all_logs(run.run_id)
        assert_events_in_order(
            logs,
            [
                "PIPELINE_ENQUEUED",
                "PIPELINE_STARTING",
                "PIPELINE_START",
                "PIPELINE_SUCCESS",
            ],
        )
