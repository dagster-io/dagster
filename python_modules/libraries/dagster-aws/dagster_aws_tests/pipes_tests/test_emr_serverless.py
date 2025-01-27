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

            assert params["tags"]["dagster/run-id"] == context.run_id  # pyright: ignore[reportTypedDictNotRequiredAccess]
            assert (
                "--conf spark.emr-serverless.driverEnv.DAGSTER_PIPES_CONTEXT="
                in params["jobDriver"]["sparkSubmit"]["sparkSubmitParameters"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
            )
            assert (
                "--conf spark.emr-serverless.driverEnv.DAGSTER_PIPES_MESSAGES="
                in params["jobDriver"]["sparkSubmit"]["sparkSubmitParameters"]  # pyright: ignore[reportTypedDictNotRequiredAccess]
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
