from dagster_celery_k8s import celery_k8s_job_executor
from dagster import Definitions, in_process_executor, op, job


@op
def op1():
    print(1)


@job
def job1():
    op1()


defs = Definitions(
    jobs=[job1],
    executor=celery_k8s_job_executor.configured(
        {
            "per_step_k8s_config": {
                "op1": {
                    "container_config": {
                        "resources": {
                            "requests": {"cpu": "77m", "memory": "77Mi"},
                            "limits": {"cpu": "88m", "memory": "88Mi"},
                        }
                    }
                }
            }
        }
    )
    if False
    else in_process_executor,
)
