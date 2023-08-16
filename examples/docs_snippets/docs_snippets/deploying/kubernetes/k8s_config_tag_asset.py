from dagster_k8s import k8s_job_executor

from dagster import asset, define_asset_job


# fmt: off
# start_k8s_config
@asset(
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
def my_asset(context):
    context.log.info("running")

my_job = define_asset_job(name="my_job", selection="my_asset", executor_def=k8s_job_executor)

# end_k8s_config
# fmt: on
