# start_pipes_session_marker

import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

import boto3
from dagster_aws.pipes import PipesS3ContextInjector, PipesS3MessageReader

import dagster as dg

LOCAL_SCRIPT_PATH = Path(__file__).parent / "script.py"


@dg.asset
def pipes_spark_asset(context: dg.AssetExecutionContext):
    s3_client = boto3.client("s3")

    bucket = os.environ["DAGSTER_PIPES_BUCKET"]

    # upload the script to S3
    # ideally, this should be done via CI/CD processes and not in the asset body
    # but for the sake of this example we are doing it here
    s3_script_path = f"{context.dagster_run.run_id}/pyspark_script.py"
    s3_client.upload_file(LOCAL_SCRIPT_PATH, bucket, s3_script_path)

    context_injector = PipesS3ContextInjector(
        client=s3_client,
        bucket=bucket,
    )

    message_reader = PipesS3MessageReader(
        client=s3_client,
        bucket=bucket,
        # the following setting will configure the Spark job to collect logs from the driver
        # and send them to Dagster via Pipes
        include_stdio_in_messages=True,
    )

    # end_pipes_session_marker

    # pipes_spark_asset body continues below
    with dg.open_pipes_session(
        context=context,
        message_reader=message_reader,
        context_injector=context_injector,
    ) as session:
        dagster_pipes_args = " ".join(
            # prepare Pipes bootstrap CLI arguments
            [
                f"{key} {value}"
                for key, value in session.get_bootstrap_cli_arguments().items()
            ]
        )

        cmd = " ".join(
            [
                "spark-submit",
                # change --master and --deploy-mode according to specific Spark setup
                "--master",
                "local[*]",
                "--conf",
                "spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem",
                # custom S3 endpoint for MinIO
                "--conf",
                "spark.hadoop.fs.s3a.endpoint=http://minio:9000",
                "--conf",
                "spark.hadoop.fs.s3a.path.style.access=true",
                f"s3a://{bucket}/{s3_script_path}",
                dagster_pipes_args,
            ]
        )

        subprocess.run(
            # we do not forward stdio on purpose to demonstrate how Pipes collect logs from the driver
            cmd,
            shell=True,
            check=True,
        )

        return session.get_results()


# start_definitions_marker


defs = dg.Definitions(
    assets=[pipes_spark_asset],
)

# end_definitions_marker
