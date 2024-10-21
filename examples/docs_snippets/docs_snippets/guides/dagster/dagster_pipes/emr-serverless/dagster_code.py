# start_asset_marker
import os

import boto3
from dagster_aws.pipes import PipesEMRServerlessClient

from dagster import AssetExecutionContext, asset


@asset
def emr_serverless_asset(
    context: AssetExecutionContext,
    pipes_emr_serverless_client: PipesEMRServerlessClient,
):
    return pipes_emr_serverless_client.run(
        context=context,
        start_job_run_params={
            "applicationId": "<app-id>",
            "executionRoleArn": "<emr-role>",
            "clientToken": context.run_id,  # idempotency identifier for the job run
            "configurationOverrides": {
                "monitoringConfiguration": {
                    "cloudWatchLoggingConfiguration": {"enabled": True}
                }
            },
        },
    ).get_results()


# end_asset_marker

# start_definitions_marker

from dagster import Definitions  # noqa


defs = Definitions(
    assets=[emr_serverless_asset],
    resources={"pipes_emr_serverless_client": PipesEMRServerlessClient()},
)

# end_definitions_marker
