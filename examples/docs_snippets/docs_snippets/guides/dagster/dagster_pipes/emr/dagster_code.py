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
        run_job_flow_params={
            "Name": "Dagster Pipes",
            "LogUri": "s3://aws-glue-assets-467123434025-eu-north-1/emr/logs",
            "JobFlowRole": "arn:aws:iam::467123434025:instance-profile/AmazonEMR-InstanceProfile-20241001T134828",
            "ServiceRole": "arn:aws:iam::467123434025:role/service-role/AmazonEMR-ServiceRole-20241001T134845",
            "ReleaseLabel": "emr-7.3.0",
            "Instances": {
                "MasterInstanceType": "m5.xlarge",
                "SlaveInstanceType": "m5.xlarge",
                "InstanceCount": 3,
                "Ec2KeyName": "YubiKey",
            },
            "Applications": [{"Name": "Hadoop"}, {"Name": "Spark"}],
            "StepConcurrencyLevel": 1,
            "Steps": [
                {
                    "Name": "Main",
                    "ActionOnFailure": "TERMINATE_CLUSTER",
                    "HadoopJarStep": {
                        "Jar": "command-runner.jar",
                        "Args": [
                            "spark-submit",
                            "--deploy-mode",
                            "cluster",
                            "--master",
                            "yarn",
                            "--files",
                            "s3://aws-glue-assets-467123434025-eu-north-1/envs/emr/pipes/venv.pex",
                            "--conf",
                            "spark.pyspark.python=./venv.pex",
                            "--conf",
                            "spark.yarn.submit.waitAppCompletion=true",
                            "s3://aws-glue-assets-467123434025-eu-north-1/envs/emr/pipes/script.py",
                        ],
                    },
                },
            ],
            "Tags": [
                {
                    "Key": "for-use-with-amazon-emr-managed-policies",
                    "Value": "true",
                }
            ],
        },
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
