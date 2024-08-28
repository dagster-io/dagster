# start_asset_marker
import os

import boto3
from dagster_aws.pipes import PipesGlueClient

from dagster import AssetExecutionContext, asset


@asset
def glue_pipes_asset(
    context: AssetExecutionContext, pipes_glue_client: PipesGlueClient
):
    return pipes_glue_client.run(
        context=context,
        job_name="Example Job",
        arguments={"some_parameter_value": "1"},
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker

from dagster import Definitions  # noqa
from dagster_aws.pipes import PipesS3ContextInjector, PipesCloudWatchMessageReader


bucket = os.environ["DAGSTER_GLUE_S3_CONTEXT_BUCKET"]


defs = Definitions(
    assets=[glue_pipes_asset],
    resources={
        "pipes_glue_client": PipesGlueClient(
            client=boto3.client("glue"),
            context_injector=PipesS3ContextInjector(
                client=boto3.client("s3"),
                bucket=bucket,
            ),
            message_reader=PipesCloudWatchMessageReader(client=boto3.client("logs")),
        )
    },
)

# end_definitions_marker
