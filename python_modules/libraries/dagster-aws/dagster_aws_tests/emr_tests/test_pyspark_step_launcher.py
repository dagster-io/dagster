from unittest import mock

from dagster_aws.emr.pyspark_step_launcher import EmrPySparkStepLauncher

from dagster import In, Out, op, DagsterEvent, EventLogEntry
from dagster._core.execution.plan.objects import StepSuccessData

EVENTS = [
    EventLogEntry(
        run_id="1",
        error_info=None,
        level=20,
        user_message="foo",
        timestamp=1.0,
        dagster_event=DagsterEvent(event_type_value="STEP_START", pipeline_name="foo"),
    ),
    EventLogEntry(
        run_id="1",
        error_info=None,
        level=20,
        user_message="bar",
        timestamp=2.0,
        dagster_event=None,
    ),
    EventLogEntry(
        run_id="1",
        error_info=None,
        level=20,
        user_message="baz",
        timestamp=3.0,
        dagster_event=DagsterEvent(
            event_type_value="STEP_SUCCESS",
            pipeline_name="foo",
            event_specific_data=StepSuccessData(duration_ms=2.0),
        ),
    ),
]


@mock.patch(
    "dagster_aws.emr.emr.EmrJobRunner.is_emr_step_complete",
    side_effect=[False, False, True],
)
@mock.patch(
    "dagster_aws.emr.pyspark_step_launcher.EmrPySparkStepLauncher.read_events",
    side_effect=[EVENTS[0:1], [], EVENTS[0:3]],
)
def test_wait_for_completion(_mock_is_emr_step_complete, _mock_read_events):
    launcher = EmrPySparkStepLauncher(
        region_name="",
        staging_bucket="",
        staging_prefix="",
        wait_for_logs=False,
        action_on_failure="",
        cluster_id="",
        spark_config={},
        local_job_package_path="",
        deploy_local_job_package=False,
    )
    yielded_events = list(
        launcher.wait_for_completion(
            mock.MagicMock(), None, None, None, None, check_interval=0
        )
    )
    assert yielded_events == [
        event.dagster_event for event in EVENTS if event.is_dagster_event
    ]
