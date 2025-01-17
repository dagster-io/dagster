# start_asset_marker

from dagster_aws.pipes import PipesEMRContainersClient

from dagster import AssetExecutionContext, asset


@asset
def emr_containers_asset(
    context: AssetExecutionContext,
    pipes_emr_containers_client: PipesEMRContainersClient,
):
    return pipes_emr_containers_client.run(
        context=context,
        start_job_run_params={
            "releaseLabel": "emr-7.5.0-latest",
            "virtualClusterId": "uqcja50dzo7v1meie1wa47wa3",
            "clientToken": context.run_id,  # idempotency identifier for the job run
            "executionRoleArn": "arn:aws:iam::467123434025:role/emr-dagster-pipes-20250109135314655100000001",
            "jobDriver": {
                "sparkSubmitJobDriver": {
                    "entryPoint": "local:///app/script.py",
                    # --conf spark.kubernetes.container.image=
                    "sparkSubmitParameters": "--conf spark.kubernetes.file.upload.path=/tmp/spark --conf spark.kubernetes.container.image=467123434025.dkr.ecr.eu-north-1.amazonaws.com/dagster/emr-containers:12",  # --conf spark.pyspark.python=/home/hadoop/.local/share/uv/python/cpython-3.9.16-linux-x86_64-gnu/bin/python --conf spark.pyspark.driver.python=/home/hadoop/.local/share/uv/python/cpython-3.9.16-linux-x86_64-gnu/bin/python",
                }
            },
            "configurationOverrides": {
                "monitoringConfiguration": {
                    "cloudWatchMonitoringConfiguration": {
                        "logGroupName": "/aws/emr/containers/pipes",
                        "logStreamNamePrefix": str(context.run_id),
                    }
                },
                # "applicationConfiguration": [
                #     {
                #         "Classification": "spark-env",
                #         "Configurations": [
                #         {
                #             "Classification": "export",
                #             "Properties": {
                #             "PYSPARK_PYTHON": "/home/hadoop/.local/share/uv/python/cpython-3.9.16-linux-x86_64-gnu/bin/python",
                #             "PYSPARK_DRIVER_PYTHON": "/home/hadoop/.local/share/uv/python/cpython-3.9.16-linux-x86_64-gnu/bin/python",
                #             }
                #         }
                #     ]
                #       }
                # ]
            },
        },
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker
import boto3
from dagster_aws.pipes import PipesCloudWatchMessageReader, PipesS3ContextInjector

from dagster import Definitions

defs = Definitions(
    assets=[emr_containers_asset],
    resources={
        "pipes_emr_containers_client": PipesEMRContainersClient(
            message_reader=PipesCloudWatchMessageReader(
                client=boto3.client("logs"),
                include_stdio_in_messages=True,
            ),
            # context_injector=PipesS3ContextInjector(
            #     bucket="dagster-pipes-20250109123428055900000004",
            #     client=boto3.client("s3"),
            # )
        )
    },
)

# end_definitions_marker
