import time

from dagster import RetryRequested, graph, op


@op
def echo(x):
    return x


@op(config_schema={"max_retries": int, "delay": float, "work_on_attempt": int})
def retry_op(context):
    time.sleep(0.1)
    if (context.retry_number + 1) >= context.op_config["work_on_attempt"]:
        return "success"
    else:
        raise RetryRequested(
            max_retries=context.op_config["max_retries"],
            seconds_to_wait=context.op_config["delay"],
        )


@graph
def retry():
    echo(retry_op())


retry_job = retry.to_job(
    config={
        "ops": {
            "retry_op": {
                "config": {
                    "delay": 0.2,
                    "work_on_attempt": 2,
                    "max_retries": 1,
                }
            }
        }
    }
)
