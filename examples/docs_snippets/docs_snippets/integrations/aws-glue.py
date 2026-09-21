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
        job_name="Example Job",  # ty: ignore[unknown-argument]
        arguments={"some_parameter_value": "1"},  # ty: ignore[unknown-argument]
    ).get_materialize_result()  # ty: ignore[missing-argument]


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
