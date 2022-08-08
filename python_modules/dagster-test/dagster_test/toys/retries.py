import time

from dagster import op, RetryRequested
from dagster._legacy import PresetDefinition, lambda_solid, pipeline, solid


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


@pipeline(
    preset_defs=[
        PresetDefinition(
            name="pass_after_retry",
            run_config={
                "solids": {
                    "retry_op": {
                        "config": {
                            "delay": 0.2,
                            "work_on_attempt": 2,
                            "max_retries": 1,
                        }
                    }
                }
            },
        )
    ]
)
def retry_pipeline():
    echo(retry_op())
