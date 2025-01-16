from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from uuid import uuid4

import boto3
import pytest
import pytest_cases
from dagster import asset, materialize, open_pipes_session
from dagster._core.execution.context.compute import AssetExecutionContext
from dagster._core.instance_for_test import instance_for_test

from dagster_aws.pipes import PipesEMRContainersClient, PipesS3MessageReader
from dagster_aws_tests.pipes_tests.utils import _MOTO_SERVER_URL, _S3_TEST_BUCKET

if TYPE_CHECKING:
    from mypy_boto3_emr_containers import EMRContainersClient


@pytest.fixture
def emr_containers_client(moto_server) -> "EMRContainersClient":
    return boto3.client("emr-containers", region_name="us-east-1", endpoint_url=_MOTO_SERVER_URL)


@pytest_cases.fixture  # pyright: ignore
@pytest_cases.parametrize(pipes_params_bootstrap_method=["args", "env"])
def pipes_emr_containers_client(
    emr_containers_client, s3_client, pipes_params_bootstrap_method
) -> PipesEMRContainersClient:
    return PipesEMRContainersClient(
        client=emr_containers_client,
        message_reader=PipesS3MessageReader(bucket=_S3_TEST_BUCKET, client=s3_client),
        pipes_params_bootstrap_method=pipes_params_bootstrap_method,
    )


@asset
def manual_asset(
    context: AssetExecutionContext, pipes_emr_containers_client: PipesEMRContainersClient
):
    with open_pipes_session(
        context=context,
        message_reader=pipes_emr_containers_client.message_reader,
        context_injector=pipes_emr_containers_client.context_injector,
    ) as session:
        params = pipes_emr_containers_client._enrich_start_params(  # noqa: SLF001
            context=context,
            session=session,
            params={
                "virtualClusterId": "test",
                "executionRoleArn": "arn:aws:iam::123456789012:role/EMRServerlessRole",
                "jobDriver": {
                    "sparkSubmitJobDriver": {
                        "entryPoint": "s3://my-bucket/my-script.py",
                        "entryPointArguments": ["arg1", "arg2"],
                        "sparkSubmitParameters": "--conf spark.executor.instances=2",
                    }
                },
                "clientToken": str(uuid4()),
            },
        )
        assert params.get("tags", {}).get("dagster/run-id") == context.run_id

        pipes_emr_containers_client._start(context, params)  # noqa: SLF001

        pipes_emr_containers_client._client.start_job_run.assert_called_once()  # noqa: SLF001
        assert (
            pipes_emr_containers_client._client.start_job_run.call_args.kwargs["virtualClusterId"]  # noqa: SLF001
            == "test"
        )

        if pipes_emr_containers_client.pipes_params_bootstrap_method == "args":
            assert (
                "--dagster-pipes-context"
                in pipes_emr_containers_client._client.start_job_run.call_args.kwargs["jobDriver"][  # noqa: SLF001
                    "sparkSubmitJobDriver"
                ]["sparkSubmitParameters"]
            )

            assert (
                "--dagster-pipes-messages"
                in pipes_emr_containers_client._client.start_job_run.call_args.kwargs["jobDriver"][  # noqa: SLF001
                    "sparkSubmitJobDriver"
                ]["sparkSubmitParameters"]
            )

        elif pipes_emr_containers_client.pipes_params_bootstrap_method == "env":
            configurations = pipes_emr_containers_client._client.start_job_run.call_args.kwargs[  # noqa: SLF001
                "configurationOverrides"
            ]["applicationConfiguration"]

            spark_defaults_injected = False
            for configuration in configurations:
                if configuration.get("classification") == "spark-defaults":
                    if (
                        "spark.yarn.appMasterEnv.DAGSTER_PIPES_CONTEXT"
                        in configuration["properties"]
                        and "spark.yarn.appMasterEnv.DAGSTER_PIPES_MESSAGES"
                        in configuration["properties"]
                    ):
                        spark_defaults_injected = True

            assert spark_defaults_injected

        return session.get_results()


def test_emr_containers_manual(pipes_emr_containers_client: "PipesEMRContainersClient"):
    pipes_emr_containers_client._client = MagicMock()  # noqa: SLF001
    with instance_for_test() as instance:
        materialize(
            [manual_asset],
            resources={"pipes_emr_containers_client": pipes_emr_containers_client},
            instance=instance,
        )


@asset
def emr_containers_asset(
    context: AssetExecutionContext, pipes_emr_containers_client: PipesEMRContainersClient
):
    return pipes_emr_containers_client.run(
        context=context,
        extras={"bar": "baz"},
        start_job_run_params={
            "virtualClusterId": "test",
            "executionRoleArn": "arn:aws:iam::123456789012:role/EMRServerlessRole",
            "jobDriver": {
                "sparkSubmitJobDriver": {
                    "entryPoint": "s3://my-bucket/my-script.py",
                    "entryPointArguments": ["arg1", "arg2"],
                    "sparkSubmitParameters": "--conf spark.executor.instances=2",
                }
            },
            "clientToken": str(uuid4()),
        },
    ).get_materialize_result()
