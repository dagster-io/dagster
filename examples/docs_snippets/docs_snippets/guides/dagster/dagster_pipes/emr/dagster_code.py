# start_asset_marker
import os

import boto3
from dagster_aws.pipes import PipesEMRClient, PipesS3MessageReader
from mypy_boto3_emr.type_defs import InstanceFleetTypeDef

from dagster import AssetExecutionContext, asset


@asset
def emr_pipes_asset(context: AssetExecutionContext, pipes_emr_client: PipesEMRClient):
    return pipes_emr_client.run(
        context=context,
        # see full reference here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/emr/client/run_job_flow.html#EMR.Client.run_job_flow
        run_job_flow_params={},  # type: ignore
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker

from dagster import Definitions  # noqa


defs = Definitions(
    assets=[emr_pipes_asset],
    resources={
        "pipes_emr_client": PipesEMRClient(
            message_reader=PipesS3MessageReader(
                client=boto3.client("s3"), bucket=os.environ["DAGSTER_PIPES_BUCKET"]
            )
        )
    },
)

# end_definitions_marker
