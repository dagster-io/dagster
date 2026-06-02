import dagster as dg
from dagster_aws.pipes import PipesEMRClient

from my_lib import make_emr_params  # type: ignore


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
