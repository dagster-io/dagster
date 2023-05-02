import time

import pytest
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._core.test_utils import poll_for_finished_run
from dagster_test.test_project import (
    ReOriginatedExternalScheduleForTest,
    get_test_project_external_schedule,
)
from marks import mark_daemon


@mark_daemon
@pytest.mark.skip("Temporarily skip until we figure out why this is so flaky")
def test_execute_schedule_on_celery_k8s(dagster_instance_for_daemon, helm_namespace_for_daemon):
    schedule_name = "frequent_celery"
    with get_test_project_external_schedule(
        dagster_instance_for_daemon, schedule_name
    ) as external_schedule:
        reoriginated_schedule = ReOriginatedExternalScheduleForTest(external_schedule)
        dagster_instance_for_daemon.start_schedule(reoriginated_schedule)

        scheduler_runs = dagster_instance_for_daemon.get_runs(
            RunsFilter(tags=DagsterRun.tags_for_schedule(reoriginated_schedule))
        )

        assert len(scheduler_runs) == 0

        try:
            start_time = time.time()

            while True:
                schedule_runs = dagster_instance_for_daemon.get_runs(
                    RunsFilter(tags=DagsterRun.tags_for_schedule(reoriginated_schedule))
                )

                if len(schedule_runs) > 0:
                    break

                if time.time() - start_time > 120:
                    raise Exception(
                        "Timed out waiting for schedule to start a run. "
                        "Check the dagster-daemon pod logs to see why it didn't start."
                    )

                time.sleep(1)
                continue

        finally:
            dagster_instance_for_daemon.stop_schedule(
                reoriginated_schedule.get_external_origin_id(),
                reoriginated_schedule.selector_id,
                reoriginated_schedule,
            )

        last_run = schedule_runs[0]

        finished_dagster_run = poll_for_finished_run(
            dagster_instance_for_daemon, last_run.run_id, timeout=180
        )

        assert finished_dagster_run.is_success
