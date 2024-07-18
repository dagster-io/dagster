from dagster_celery_k8s import celery_k8s_job_executor
from dagster import Definitions, in_process_executor, op, job


@op(
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "111m", "memory": "222Mi"},
                    "limits": {"cpu": "111m", "memory": "222Mi"},
                }
            }
        }
    }
)
def op1():
    print(1)

@op(
    tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "requests": {"cpu": "233m", "memory": "233Mi"},
                    "limits": {"cpu": "233m", "memory": "233Mi"},
                }
            }
        }
    }
)
def op2():
    print(1)


@job
def job1():
    op1()
    op2()


defs = Definitions(
    jobs=[job1],
    executor=celery_k8s_job_executor.configured(
        {
            "per_step_k8s_config": {
                "op1": {
                    "container_config": {
                        "resources": {
                            "requests": {"cpu": "777m", "memory": "777Mi"},
                            "limits": {"cpu": "888m", "memory": "888Mi"},
                        }
                    }
                },
                "op2": {
                    "container_config": {
                        "resources": {
                            "requests": {"cpu": "555m", "memory": "555Mi"},
                            "limits": {"cpu": "555m", "memory": "555Mi"},
                        }
                    }
                }
            }
        }
    )
    if True
    else in_process_executor,
)
