from dagster_k8s import k8s_job_executor

import dagster as dg


# fmt: off
# start_k8s_config
@dg.op(
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
def my_op(context: dg.OpExecutionContext):
    context.log.info("running")

@dg.job(executor_def=k8s_job_executor)
def my_job():
    my_op()
# end_k8s_config
# fmt: on
