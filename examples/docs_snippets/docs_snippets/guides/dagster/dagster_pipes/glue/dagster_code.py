# start_asset_marker
import os

import boto3
from dagster_aws.pipes import PipesGlueClient

import dagster as dg


@dg.asset
def glue_pipes_asset(
    context: dg.AssetExecutionContext, pipes_glue_client: PipesGlueClient
):
    return pipes_glue_client.run(
        context=context,
        start_job_run_params={
            "JobName": "Example Job",
            "Arguments": {"some_parameter": "some_value"},
        },
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker

import dagster as dg  # noqa
from dagster_aws.pipes import PipesS3ContextInjector, PipesCloudWatchMessageReader


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "pipes_glue_client": PipesGlueClient(
                client=boto3.client("glue"),
                context_injector=PipesS3ContextInjector(
                    client=boto3.client("s3"),
                    bucket=dg.EnvVar("DAGSTER_GLUE_S3_CONTEXT_BUCKET"),
                ),
                message_reader=PipesCloudWatchMessageReader(
                    client=boto3.client("logs")
                ),
            )
        },
    )


# end_definitions_marker
