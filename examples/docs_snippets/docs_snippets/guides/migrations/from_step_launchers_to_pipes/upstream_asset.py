import dagster as dg
from dagster_aws.pipes import PipesEMRClient

from my_lib import make_emr_params  # type: ignore


@dg.asset(io_manager_key="s3_io_manager")
def upstream(context: dg.AssetExecutionContext, pipes_emr_client: PipesEMRClient):
    result = pipes_emr_client.run(
        context=context,
        run_job_flow_params=make_emr_params(
            "s3://your-bucket/upstream_asset_script.py"
        ),
    ).get_materialize_result()

    return result.metadata["path"].value  # type: ignore
