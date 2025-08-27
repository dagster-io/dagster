import dagster as dg  # noqa
from dagster_aws.pipes import (
    PipesGlueClient,
    PipesS3ContextInjector,
    PipesCloudWatchMessageReader,
)
import boto3


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
