import boto3
import dagster as dg
from dagster_aws.pipes import PipesEMRClient

from my_lib import make_emr_params  # type: ignore


@dg.asset(io_manager_key="s3_io_manager")
def upstream(
    context: dg.AssetExecutionContext, pipes_emr_client: PipesEMRClient
) -> str:
    result = pipes_emr_client.run(
        context=context,
        run_job_flow_params=make_emr_params(
            "s3://your-bucket/upstream_asset_script.py"
        ),
    ).get_materialize_result()

    return result.metadata["path"].value  # type: ignore


# after_upstream_marker


@dg.asset
def downstream(
    context: dg.AssetExecutionContext, upstream: str, pipes_emr_client: PipesEMRClient
):
    return pipes_emr_client.run(
        context=context,
        run_job_flow_params=make_emr_params(
            "s3://your-bucket/downstream_asset_script.py"
        ),
        extras={"path": upstream},
    ).get_materialize_result()


# after_downstream_marker

from dagster_aws.pipes import PipesS3MessageReader  # noqa: E402
from dagster_aws.s3 import S3PickleIOManager, S3Resource  # noqa: E402

definitions = dg.Definitions(
    assets=[upstream, downstream],
    resources={
        "pipes_emr_client": PipesEMRClient(
            client=boto3.client("emr"),
            message_reader=PipesS3MessageReader(
                client=boto3.client("s3"),
                bucket="your-bucket",
            ),
        ),
        "s3_io_manager": S3PickleIOManager(
            s3_resource=S3Resource(),
            s3_bucket="your-bucket",
            s3_prefix="your-prefix",
        ),
    },
)
