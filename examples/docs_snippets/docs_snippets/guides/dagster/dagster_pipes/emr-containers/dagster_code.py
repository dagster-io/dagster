# start_asset_marker

from dagster_aws.pipes import PipesEMRContainersClient

import dagster as dg


@dg.asset
def emr_containers_asset(
    context: dg.AssetExecutionContext,
    pipes_emr_containers_client: PipesEMRContainersClient,
):
    image = (
        ...
    )  # it's likely the image can be taken from context.run_tags["dagster/image"]

    return pipes_emr_containers_client.run(
        context=context,
        start_job_run_params={
            "releaseLabel": "emr-7.5.0-latest",
            "virtualClusterId": ...,
            "clientToken": context.run_id,  # idempotency identifier for the job run
            "executionRoleArn": ...,
            "jobDriver": {
                "sparkSubmitJobDriver": {
                    "entryPoint": "local:///app/script.py",
                    "sparkSubmitParameters": f"--conf spark.kubernetes.container.image={image}",
                }
            },
        },
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker
import boto3
from dagster_aws.pipes import PipesS3MessageReader

from dagster import Definitions

defs = Definitions(
    assets=[emr_containers_asset],
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

# end_definitions_marker
