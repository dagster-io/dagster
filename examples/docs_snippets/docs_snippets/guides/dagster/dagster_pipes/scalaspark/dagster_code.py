import dagster as dg
import boto3
import subprocess
from dagster_aws.pipes import PipesS3MessageReader, PipesS3ContextInjector
import os
from typing import Sequence

@dg.asset(check_specs=[dg.AssetCheckSpec(
            name="demo_check",
            asset="scala_spark_demo"
        )
    ]
)
def scala_spark_demo(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    s3_client = boto3.client("s3")
    s3_bucket_name = os.environ["DAGSTER_PIPES_BUCKET"]
    
    jar_path = dg.file_relative_path(__file__, "external_scala/build/libs/external_scala-all.jar")

    with dg.open_pipes_session(
        context=context,
        message_reader=PipesS3MessageReader(bucket=s3_bucket_name, client=s3_client),
        context_injector=PipesS3ContextInjector(bucket=s3_bucket_name, client=s3_client),
    ) as session:
        args = " ".join(
            f"{key} {value}"
            for key, value in session.get_bootstrap_cli_arguments().items()
        )

        subprocess.run(
            ["spark-submit", jar_path] + args.split(),
            shell=False,
            check=True,
        )

    return session.get_results()

defs = dg.Definitions(
  assets=[scala_spark_demo],
)