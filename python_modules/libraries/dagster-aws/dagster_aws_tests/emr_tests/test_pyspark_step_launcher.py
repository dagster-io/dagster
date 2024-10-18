import os
from unittest import mock

import pytest
from dagster import DagsterEvent, EventLogEntry, build_init_resource_context
from dagster._core.execution.plan.objects import StepSuccessData

from dagster_aws.emr.pyspark_step_launcher import EmrPySparkStepLauncher, emr_pyspark_step_launcher

EVENTS = [
    EventLogEntry(
        run_id="1",
        error_info=None,
        level=20,
        user_message="foo",
        timestamp=1.0,
        dagster_event=DagsterEvent(event_type_value="STEP_START", job_name="foo"),
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
            job_name="foo",
            event_specific_data=StepSuccessData(duration_ms=2.0),
        ),
    ),
]


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
        local_job_package_path="",
        deploy_local_job_package=False,
    )
    yielded_events = list(
        launcher.wait_for_completion(mock.MagicMock(), None, None, None, None, check_interval=0)
    )
    assert yielded_events == [event.dagster_event for event in EVENTS if event.is_dagster_event]


def test_emr_pyspark_step_launcher_legacy_arguments():
    mock_config = {
        "local_job_package_path": os.path.abspath(os.path.dirname(__file__)),
        "cluster_id": "123",
        "staging_bucket": "bucket",
        "region_name": "us-west-1",
    }

    with pytest.raises(Exception):
        emr_pyspark_step_launcher(
            build_init_resource_context(
                config={
                    **mock_config,
                    "local_pipeline_package_path": "path",
                }
            )
        )

    with pytest.raises(Exception):
        emr_pyspark_step_launcher(
            build_init_resource_context(
                config={
                    **mock_config,
                    "deploy_local_job_package": True,
                    "deploy_local_pipeline_package": True,
                }
            )
        )

    with pytest.raises(Exception):
        emr_pyspark_step_launcher(
            build_init_resource_context(
                config={
                    **mock_config,
                    "s3_job_package_path": "path",
                    "s3_pipeline_package_path": "path",
                }
            )
        )

    assert emr_pyspark_step_launcher(
        build_init_resource_context(
            config={
                **mock_config,
                "deploy_local_job_package": True,
            }
        )
    )
