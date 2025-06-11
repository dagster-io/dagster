# start_asset_marker

from dagster_aws.pipes import PipesEMRServerlessClient

import dagster as dg


@dg.asset
def emr_serverless_asset(
    context: dg.AssetExecutionContext,
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

import dagster as dg


@dg.definitions
def resources():
    return dg.Definitions(
        resources={"pipes_emr_serverless_client": PipesEMRServerlessClient()}
    )


# end_definitions_marker
