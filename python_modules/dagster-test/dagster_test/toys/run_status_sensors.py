from time import time

from dagster import (
    DagsterRunStatus,
    JobSelector,
    RepositorySelector,
    RunRequest,
    SkipReason,
    job,
    op,
    run_failure_sensor,
    run_status_sensor,
)
from dagster._core.definitions.run_request import PipelineRunReaction


@op
def succeeds():
    return 1


@op
def fails():
    raise Exception("fails")


@job
def succeeds_job():
    succeeds()


@job
def fails_job():
    fails()


@op
def status_printer(context):
    context.log.info(f"message: {context.op_config['message']}")


@job
def status_job():
    status_printer()


@run_status_sensor(run_status=DagsterRunStatus.SUCCESS, request_job=status_job)
def yield_run_request_succeeds_sensor(context):
    """We recommend returning RunRequests, but it's possible to yield, so this is here to test it.
    """
    if context.dagster_run.pipeline_name != status_job.name:
        yield RunRequest(
            run_key=None,
            run_config={
                "ops": {
                    "status_printer": {
                        "config": {
                            "message": f"{context.dagster_run.pipeline_name} job succeeded!!!"
                        }
                    }
                }
            },
        )
    else:
        yield SkipReason("Don't report status of status_job.")


@run_status_sensor(run_status=DagsterRunStatus.SUCCESS, request_job=status_job)
def return_run_request_succeeds_sensor(context):
    if context.dagster_run.pipeline_name != status_job.name:
        return RunRequest(
            run_key=None,
            run_config={
                "ops": {
                    "status_printer": {
                        "config": {
                            "message": f"{context.dagster_run.pipeline_name} job succeeded!!!"
                        }
                    }
                }
            },
        )
    else:
        return SkipReason("Don't report status of status_job.")


@run_failure_sensor(request_job=status_job)
def fails_sensor(context):
    return RunRequest(
        run_key=None,
        run_config={
            "ops": {
                "status_printer": {
                    "config": {"message": f"{context.dagster_run.pipeline_name} job failed!!!"}
                }
            }
        },
    )


@run_status_sensor(
    run_status=DagsterRunStatus.SUCCESS,
)
def success_sensor_with_pipeline_run_reaction(context):
    """Some users do this, so here's a way to test it out."""
    return PipelineRunReaction(context.dagster_run)


@run_status_sensor(run_status=DagsterRunStatus.SUCCESS, request_job=status_job)
def yield_multi_run_request_success_sensor(context):
    if context.dagster_run.pipeline_name != status_job.name:
        for _ in range(3):
            yield RunRequest(
                run_key=str(time()),
                run_config={
                    "ops": {
                        "status_printer": {
                            "config": {
                                "message": f"{context.dagster_run.pipeline_name} job succeeded!!!"
                            }
                        }
                    }
                },
            )
    else:
        return SkipReason("Don't report status of status_job.")


@run_status_sensor(run_status=DagsterRunStatus.SUCCESS, request_job=status_job)
def return_multi_run_request_success_sensor(context):
    """Also test returning a list of run requests."""
    if context.dagster_run.pipeline_name != status_job.name:
        reqs = []
        for _ in range(3):
            r = RunRequest(
                run_key=str(time()),
                run_config={
                    "ops": {
                        "status_printer": {
                            "config": {
                                "message": f"{context.dagster_run.pipeline_name} job succeeded!!!"
                            }
                        }
                    }
                },
            )
            reqs.append(r)
        return reqs
    else:
        return SkipReason("Don't report status of status_job.")


@run_failure_sensor(
    monitored_jobs=[
        fails_job,
        JobSelector(
            location_name="dagster_test.toys.repo",
            repository_name="more_toys_repository",
            job_name="fails_job",
        ),
    ],
    request_job=status_job,
)
def cross_repo_job_sensor(context):
    return RunRequest(
        run_key=None,
        run_config={
            "ops": {
                "status_printer": {
                    "config": {"message": f"{context.dagster_run.pipeline_name} job failed!!!"}
                }
            }
        },
    )


@run_failure_sensor(
    monitored_jobs=[
        fails_job,
        RepositorySelector(
            location_name="dagster_test.toys.repo",
            repository_name="more_toys_repository",
        ),
    ],
    request_job=status_job,
)
def cross_repo_sensor(context):
    return RunRequest(
        run_key=None,
        run_config={
            "ops": {
                "status_printer": {
                    "config": {"message": f"{context.dagster_run.pipeline_name} job failed!!!"}
                }
            }
        },
    )


@run_status_sensor(
    monitored_jobs=[
        JobSelector(
            location_name="dagster_test.toys.repo",
            repository_name="more_toys_repository",
            job_name="succeeds_job",
        ),
    ],
    request_job=status_job,
    run_status=DagsterRunStatus.SUCCESS,
)
def cross_repo_success_job_sensor(context):
    return RunRequest(
        run_key=None,
        run_config={
            "ops": {
                "status_printer": {
                    "config": {"message": f"{context.dagster_run.pipeline_name} job succeeded!!!"}
                }
            }
        },
    )


@run_status_sensor(
    monitor_all_repositories=True,
    request_job=status_job,
    run_status=DagsterRunStatus.SUCCESS,
)
def instance_success_sensor(context):
    # to avoid an infinite loop on the success of status_job
    if context.dagster_run.pipeline_name != status_job.name:
        return RunRequest(
            run_key=None,
            run_config={
                "ops": {
                    "status_printer": {
                        "config": {
                            "message": f"{context.dagster_run.pipeline_name} job succeeded!!!"
                        }
                    }
                }
            },
        )
