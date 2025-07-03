import boto3
from dagster_aws.pipes import PipesEMRClient, PipesS3MessageReader

import dagster as dg


# start_resources
@dg.definitions
def resources():
    return dg.Definitions(
        resources={
            "pipes_emr_client": PipesEMRClient(
                message_reader=PipesS3MessageReader(
                    client=boto3.client("s3"),
                    bucket=dg.EnvVar("DAGSTER_PIPES_BUCKET"),
                )
            )
        },
    )
