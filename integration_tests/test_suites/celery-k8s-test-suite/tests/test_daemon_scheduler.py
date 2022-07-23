import time

from dagster_test.test_project import (
    ReOriginatedExternalScheduleForTest,
    get_test_project_external_schedule,
)
from marks import mark_daemon

from dagster.core.storage.pipeline_run import PipelineRun, RunsFilter
from dagster.core.test_utils import poll_for_finished_run


@mark_daemon
def test_execute_schedule_on_celery_k8s(  # pylint: disable=redefined-outer-name, disable=unused-argument
    dagster_instance_for_daemon, helm_namespace_for_daemon
):
    schedule_name = "frequent_celery"
    with get_test_project_external_schedule(
        dagster_instance_for_daemon, schedule_name
    ) as external_schedule:
        reoriginated_schedule = ReOriginatedExternalScheduleForTest(external_schedule)
        dagster_instance_for_daemon.start_schedule(reoriginated_schedule)

        scheduler_runs = dagster_instance_for_daemon.get_runs(
            RunsFilter(tags=PipelineRun.tags_for_schedule(reoriginated_schedule))
        )

        assert len(scheduler_runs) == 0

        try:

            start_time = time.time()

            while True:
                schedule_runs = dagster_instance_for_daemon.get_runs(
                    RunsFilter(tags=PipelineRun.tags_for_schedule(reoriginated_schedule))
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

        finished_pipeline_run = poll_for_finished_run(
            dagster_instance_for_daemon, last_run.run_id, timeout=120
        )

        assert finished_pipeline_run.is_success
