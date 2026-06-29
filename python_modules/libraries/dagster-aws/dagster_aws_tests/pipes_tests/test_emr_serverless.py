from typing import TYPE_CHECKING
from uuid import uuid4

import boto3
import pytest
from dagster import asset, materialize, open_pipes_session
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.pipes.utils import PipesEnvContextInjector

from dagster_aws.pipes import PipesCloudWatchMessageReader, PipesEMRServerlessClient
from dagster_aws_tests.pipes_tests.utils import _MOTO_SERVER_URL

if TYPE_CHECKING:
    from mypy_boto3_emr_serverless import EMRServerlessClient


EMR_SERVERLESS_APP_NAME = "Example"


@pytest.fixture
def emr_serverless_setup(moto_server, s3_client) -> tuple["EMRServerlessClient", str]:
    client = boto3.client("emr-serverless", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)
    resp = client.create_application(
        type="SPARK",
        releaseLabel="emr-7.2.0-latest",
        clientToken=str(uuid4()),
    )
    return client, resp["applicationId"]


def test_emr_serverless_manual(emr_serverless_setup: tuple["EMRServerlessClient", str]):
    client, application_id = emr_serverless_setup

    @asset
    def my_asset(context: AssetExecutionContext, emr_serverless_client: PipesEMRServerlessClient):
        message_reader = PipesCloudWatchMessageReader()
        context_injector = PipesEnvContextInjector()

        with open_pipes_session(
            context=context,
            message_reader=message_reader,
            context_injector=context_injector,
        ) as session:
            params = emr_serverless_client._enrich_start_params(  # noqa: SLF001
                context=context,
                session=session,
                params={
                    "applicationId": application_id,
                    "executionRoleArn": "arn:aws:iam::123456789012:role/EMRServerlessRole",
                    "jobDriver": {
                        "sparkSubmit": {
                            "entryPoint": "s3://my-bucket/my-script.py",
                        }
                    },
                    "clientToken": str(uuid4()),
                },
            )

            assert params["tags"]["dagster/run-id"] == context.run_id
            assert (
                "--conf spark.emr-serverless.driverEnv.DAGSTER_PIPES_CONTEXT="
                in params["jobDriver"]["sparkSubmit"]["sparkSubmitParameters"]
            )
            assert (
                "--conf spark.emr-serverless.driverEnv.DAGSTER_PIPES_MESSAGES="
                in params["jobDriver"]["sparkSubmit"]["sparkSubmitParameters"]
            )

            # moto doesn't have start_job_run implemented so this is as far as we can get with it right now

            return session.get_results()

    with instance_for_test() as instance:
        materialize(
            [my_asset],
            resources={
                "emr_serverless_client": PipesEMRServerlessClient(
                    client=client,
                )
            },
            instance=instance,
        )


def test_emr_serverless_dashboard_refresh():
    from unittest.mock import MagicMock, patch
    from dagster_aws.pipes import PipesEMRServerlessClient

    client = MagicMock()
    client.start_job_run.return_value = {
        "jobRunId": "test-job-run-id",
        "applicationId": "test-app-id",
    }

    current_time = [0.0]

    def mock_time():
        return current_time[0]

    def mock_sleep(seconds):
        current_time[0] += seconds

    mock_time_module = MagicMock()
    mock_time_module.time.side_effect = mock_time
    mock_time_module.sleep.side_effect = mock_sleep

    client.get_job_run.side_effect = [
        {"jobRun": {"state": "RUNNING", "applicationId": "test-app-id", "jobRunId": "test-job-run-id"}},
        {"jobRun": {"state": "RUNNING", "applicationId": "test-app-id", "jobRunId": "test-job-run-id"}},
        {"jobRun": {"state": "RUNNING", "applicationId": "test-app-id", "jobRunId": "test-job-run-id"}},
        {"jobRun": {"state": "SUCCESS", "applicationId": "test-app-id", "jobRunId": "test-job-run-id"}},
    ]

    client.get_dashboard_for_job_run.return_value = "http://mock-spark-ui-url"

    @asset
    def my_asset(context: AssetExecutionContext, emr_serverless_client: PipesEMRServerlessClient):
        return emr_serverless_client.run(
            context=context,
            start_job_run_params={
                "applicationId": "test-app-id",
                "executionRoleArn": "arn:aws:iam::123456789012:role/EMRServerlessRole",
                "jobDriver": {
                    "sparkSubmit": {
                        "entryPoint": "s3://my-bucket/my-script.py",
                    }
                },
            }
        ).get_results()

    with patch.object(PipesEMRServerlessClient, "_read_messages"), \
         patch.object(PipesEMRServerlessClient, "_extract_dagster_metadata", return_value={}), \
         patch("dagster_aws.pipes.clients.emr_serverless.time", mock_time_module), \
         instance_for_test() as instance:

        materialize(
            [my_asset],
            resources={
                "emr_serverless_client": PipesEMRServerlessClient(
                    client=client,
                    poll_interval=600.0,
                )
            },
            instance=instance,
        )

    assert client.get_dashboard_for_job_run.call_count == 1

    # Reset mock and time for second run with custom interval
    client.get_dashboard_for_job_run.reset_mock()
    current_time[0] = 0.0
    client.get_job_run.side_effect = [
        {"jobRun": {"state": "RUNNING", "applicationId": "test-app-id", "jobRunId": "test-job-run-id"}},
        {"jobRun": {"state": "RUNNING", "applicationId": "test-app-id", "jobRunId": "test-job-run-id"}},
        {"jobRun": {"state": "RUNNING", "applicationId": "test-app-id", "jobRunId": "test-job-run-id"}},
        {"jobRun": {"state": "SUCCESS", "applicationId": "test-app-id", "jobRunId": "test-job-run-id"}},
    ]

    with patch.object(PipesEMRServerlessClient, "_read_messages"), \
         patch.object(PipesEMRServerlessClient, "_extract_dagster_metadata", return_value={}), \
         patch("dagster_aws.pipes.clients.emr_serverless.time", mock_time_module), \
         instance_for_test() as instance:

        materialize(
            [my_asset],
            resources={
                "emr_serverless_client": PipesEMRServerlessClient(
                    client=client,
                    poll_interval=600.0,
                    dashboard_refresh_interval=900.0,
                )
            },
            instance=instance,
        )

    assert client.get_dashboard_for_job_run.call_count == 2



