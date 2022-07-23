from dagster_k8s import k8s_job_executor

from dagster import job, op


# fmt: off
# start_k8s_config
@op(
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "200m", "memory": "32Mi"},
                }
            },
        }
    }
)
def my_op(context):
    context.log.info("running")

@job(executor_def=k8s_job_executor)
def my_job():
    my_op()
# end_k8s_config
# fmt: on
