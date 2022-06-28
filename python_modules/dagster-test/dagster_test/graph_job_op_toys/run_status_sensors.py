from dagster import (
    DagsterRunStatus,
    RunRequest,
    SkipReason,
    job,
    op,
    run_failure_sensor,
    run_status_sensor,
)


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


@run_status_sensor(pipeline_run_status=DagsterRunStatus.SUCCESS, response_job=status_job)
def succeeds_sensor(context):
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


@run_failure_sensor(response_job=status_job)
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
