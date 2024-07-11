# start_asset_marker
import os

# dagster_glue_pipes.py
import boto3
from dagster_aws.pipes import PipesGlueClient, PipesGlueContextInjector

from dagster import AssetExecutionContext, Definitions, asset


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

# dagster_glue_pipes.py

defs = Definitions(
    assets=[glue_pipes_asset],
    resources={
        "pipes_glue_client": PipesGlueClient(
            context_injector=PipesGlueContextInjector(
                bucket=os.environ["DAGSTER_GLUE_S3_CONTEXT_BUCKET"],
                client=boto3.client("s3"),
            ),
            client=boto3.client("glue"),
        )
    },
)
# end_definitions_marker
