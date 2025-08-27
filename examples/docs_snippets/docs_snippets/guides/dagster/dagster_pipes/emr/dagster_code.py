import os

import boto3
from dagster_aws.pipes import PipesEMRClient, PipesS3MessageReader

import dagster as dg


@dg.asset
def emr_pipes_asset(
    context: dg.AssetExecutionContext, pipes_emr_client: PipesEMRClient
):
    return pipes_emr_client.run(
        context=context,
        # see full reference here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/emr/client/run_job_flow.html#EMR.Client.run_job_flow
        run_job_flow_params={},  # type: ignore
    ).get_materialize_result()
