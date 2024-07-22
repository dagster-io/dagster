"""Example of container_config overriding logic.

1. celery_k8s_job_executor is most important, it precedes everything else. Is specified, `run_config` from RunRequest is ignored.
Precedence order:
- at job-s definition (via executor_def=...)
- at Definitions (via executor=...)
2. after it goes run_config from request limit in schedule. If celery_k8s_job_executor is configured (via Definitions or via job), RunRequest config is ignored.
3. Then goes tag "dagster-k8s/config" from op.
"""

from dagster import Definitions, RunRequest, job, op, schedule
from dagster_celery_k8s import celery_k8s_job_executor


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


@job(
    executor_def=celery_k8s_job_executor.configured(
        {
            "per_step_k8s_config": {
                "op1": {
                    "container_config": {
                        "resources": {
                            "requests": {"cpu": "999m", "memory": "999Mi"},
                            "limits": {"cpu": "999m", "memory": "999Mi"},
                        }
                    }
                },
                "op2": {
                    "container_config": {
                        "resources": {
                            "requests": {"cpu": "1111m", "memory": "1111Mi"},
                            "limits": {"cpu": "1111m", "memory": "1111Mi"},
                        }
                    }
                },
            }
        }
    )
)
def job1():
    op1()
    op2()


@schedule(job=job1, cron_schedule="* * * * *")
def schedule1():
    return RunRequest(
        run_config={
            "execution": {
                "config": {
                    "per_step_k8s_config": {
                        "op1": {
                            "container_config": {
                                "resources": {
                                    "requests": {"cpu": "888m", "memory": "888Mi"},
                                    "limits": {"cpu": "888m", "memory": "888Mi"},
                                }
                            }
                        },
                        "op2": {
                            "container_config": {
                                "resources": {
                                    "requests": {"cpu": "677m", "memory": "677Mi"},
                                    "limits": {"cpu": "677m", "memory": "677Mi"},
                                }
                            }
                        },
                    }
                }
            }
        }
    )


defs = Definitions(
    jobs=[job1],
    schedules=[schedule1],
    # executor=celery_k8s_job_executor,
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
                },
            }
        }
    ),
)
