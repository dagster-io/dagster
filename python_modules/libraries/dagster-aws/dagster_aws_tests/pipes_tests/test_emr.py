from typing import TYPE_CHECKING

import boto3
import pytest
from dagster import asset, materialize, open_pipes_session
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test
from dagster._core.pipes.utils import PipesEnvContextInjector

from dagster_aws.pipes import PipesCloudWatchMessageReader, PipesEMRClient, PipesS3MessageReader
from dagster_aws_tests.pipes_tests.utils import _MOTO_SERVER_URL, _S3_TEST_BUCKET

if TYPE_CHECKING:
    from mypy_boto3_emr import EMRClient


@pytest.fixture
def emr_client(moto_server) -> "EMRClient":
    return boto3.client("emr", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)


@pytest.fixture
def pipes_emr_client(emr_client, s3_client) -> PipesEMRClient:
    return PipesEMRClient(
        client=emr_client,
        message_reader=PipesS3MessageReader(bucket=_S3_TEST_BUCKET, client=s3_client),
    )


def test_emr_enrich_params(pipes_emr_client: "PipesEMRClient"):
    @asset
    def my_asset(context: AssetExecutionContext, pipes_emr_client: PipesEMRClient):
        message_reader = PipesCloudWatchMessageReader()
        context_injector = PipesEnvContextInjector()

        with open_pipes_session(
            context=context,
            message_reader=message_reader,
            context_injector=context_injector,
        ) as session:
            params = pipes_emr_client._enrich_params(  # noqa: SLF001
                session=session,
                params={
                    "Name": "test",
                    "ReleaseLabel": "emr-7.2.0-latest",
                    "LogUri": "s3://my-bucket/logs",
                    "Instances": {
                        "MasterInstanceType": "m5.xlarge",
                        "SlaveInstanceType": "m5.xlarge",
                        "InstanceCount": 2,
                    },
                    "Steps": [
                        {
                            "Name": "test",
                            "ActionOnFailure": "CONTINUE",
                            "HadoopJarStep": {
                                "Jar": "command-runner.jar",
                                "Args": ["spark-submit", "--version"],
                            },
                        }
                    ],
                    "Configurations": [],
                },
            )

            run_id_tag_injected = False

            for tag in params.get("Tags", []):
                if tag.get("Key") == "dagster/run-id":
                    run_id_tag_injected = True
                    assert tag.get("Value") == context.run_id

            assert run_id_tag_injected

            return session.get_results()

    with instance_for_test() as instance:
        materialize(
            [my_asset],
            resources={"pipes_emr_client": pipes_emr_client},
            instance=instance,
        )
