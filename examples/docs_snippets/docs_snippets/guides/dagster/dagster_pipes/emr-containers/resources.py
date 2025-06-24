import boto3
from dagster_aws.pipes import PipesEMRContainersClient, PipesS3MessageReader

import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "pipes_emr_containers_client": PipesEMRContainersClient(
                message_reader=PipesS3MessageReader(
                    client=boto3.client("s3"),
                    bucket=...,
                    include_stdio_in_messages=True,
                ),
            )
        },
    )
