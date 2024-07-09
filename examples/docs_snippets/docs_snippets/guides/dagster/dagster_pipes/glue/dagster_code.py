# start_asset_marker
import os

# dagster_lambda_pipes.py
import boto3
from dagster_aws.pipes import PipesGlueClient, PipesS3ContextInjector

from dagster import AssetExecutionContext, Definitions, asset


@asset
def glue_pipes_asset(
    context: AssetExecutionContext, glue_pipes_client: PipesGlueClient
):
    return glue_pipes_client.run(
        context=context,
        job_name="Example Job",
        arguments={"some_parameter_value": "1"},
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker

# dagster_lambda_pipes.py

defs = Definitions(
    assets=[glue_pipes_asset],
    resources={
        "glue_pipes_client": PipesGlueClient(
            context_injector=PipesS3ContextInjector(
                bucket=os.environ["DAGSTER_GLUE_S3_CONTEXT_BUCKET"],
                client=boto3.client("s3"),
            ),
            client=boto3.client("glue"),
        )
    },
)
# end_definitions_marker
