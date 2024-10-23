import boto3
from dagster_aws.pipes import (
    PipesGlueClient,
    PipesS3ContextInjector,
    PipesS3MessageReader,
)

import dagster as dg


@dg.asset
def glue_pipes_asset(
    context: dg.AssetExecutionContext, pipes_glue_client: PipesGlueClient
):
    return pipes_glue_client.run(
        context=context,
        job_name="Example Job",
        arguments={"some_parameter_value": "1"},
    ).get_materialize_result()


defs = dg.Definitions(
    assets=[glue_pipes_asset],
    resources={
        "pipes_glue_client": PipesGlueClient(
            client=boto3.client("glue", region_name="us-east-1"),
            context_injector=PipesS3ContextInjector(
                client=boto3.client("s3"),
                bucket="my-bucket",
            ),
            message_reader=PipesS3MessageReader(
                client=boto3.client("s3"), bucket="my-bucket"
            ),
        )
    },
)
