from dagster_k8s import k8s_job_executor

import dagster as dg


# fmt: off
# start_k8s_config
# op_tags with "dagster-k8s/config" applies to the step pod for this asset.
# This works when the asset is run via a named job OR when materialized
# directly from the Dagster UI ("Materialize" button), as long as the
# deployment uses k8s_job_executor.
@dg.asset(
    op_tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "200m", "memory": "32Mi"},
                    "limits": {"cpu": "1", "memory": "2Gi"},
                }
            },
        }
    }
)
def my_asset(context: dg.AssetExecutionContext):
    context.log.info("running")


# The k8s_job_executor runs each step in its own pod.
# op_tags on the asset control the resources for that pod.
my_job = dg.define_asset_job(name="my_job", selection="my_asset", executor_def=k8s_job_executor)

# end_k8s_config
# fmt: on
