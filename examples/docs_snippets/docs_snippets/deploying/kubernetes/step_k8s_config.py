from dagster_k8s import k8s_job_executor

from dagster import job

# fmt: off
# start_step_k8s_config
my_k8s_executor = k8s_job_executor.configured(
    {
        "step_k8s_config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "200m", "memory": "32Mi"},
                }
            }
        }
    }
)

@job(executor_def=my_k8s_executor)
def my_job():
    ...
# end_step_k8s_config
# fmt: on
