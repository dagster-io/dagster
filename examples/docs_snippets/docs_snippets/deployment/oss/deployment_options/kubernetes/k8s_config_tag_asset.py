from dagster_k8s import k8s_job_executor

import dagster as dg


# fmt: off
# start_k8s_config
@dg.asset(
    op_tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "200m", "memory": "32Mi"},
                }
            },
        }
    }
)
def my_asset(context: dg.AssetExecutionContext):
    context.log.info("running")

my_job = dg.define_asset_job(name="my_job", selection="my_asset", executor_def=k8s_job_executor)

# end_k8s_config
# fmt: on
