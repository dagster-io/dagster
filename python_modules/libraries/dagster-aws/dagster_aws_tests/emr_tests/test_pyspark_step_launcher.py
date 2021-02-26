from unittest import mock

from dagster_aws.emr.pyspark_step_launcher import EmrPySparkStepLauncher

EVENTS = [object(), object(), object()]


@mock.patch(
    "dagster_aws.emr.emr.EmrJobRunner.is_emr_step_complete", side_effect=[False, False, True]
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
        local_pipeline_package_path="",
        deploy_local_pipeline_package=False,
    )
    yielded_events = list(
        launcher.wait_for_completion(mock.MagicMock(), None, None, None, None, check_interval=0)
    )
    assert yielded_events == EVENTS
