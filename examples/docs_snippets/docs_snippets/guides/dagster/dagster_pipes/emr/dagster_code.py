# start_asset_marker
import os

import boto3
from dagster_aws.pipes import PipesEMRClient

from dagster import AssetExecutionContext, asset


@asset
def glue_pipes_asset(context: AssetExecutionContext, pipes_emr_client: PipesEMRClient):
    return pipes_emr_client.run(
        context=context,
        run_job_flow_params={
            "Name": "Example Job",
            "Instances": {
                "MasterInstanceType": "m5.xlarge",
                "SlaveInstanceType": "m5.xlarge",
                "InstanceCount": 3,
            },
            "Steps": [
                {
                    "Name": "Example Step",
                    "ActionOnFailure": "CONTINUE",
                    "HadoopJarStep": {
                        "Jar": "command-runner.jar",
                        "Args": [
                            "spark-submit",
                            "--deploy-mode",
                            "cluster",
                            "example.py",
                        ],
                    },
                }
            ],
        },
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker

from dagster import Definitions  # noqa


defs = Definitions(
    assets=[glue_pipes_asset],
    resources={"pipes_emr_client": PipesEMRClient()},
)

# end_definitions_marker
