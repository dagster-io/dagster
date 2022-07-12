import time

from dagster import PresetDefinition, RetryRequested, pipeline, solid


@solid
def echo(x):
    return x


@solid(config_schema={"max_retries": int, "delay": float, "work_on_attempt": int})
def retry_solid(context):
    time.sleep(0.1)
    if (context.retry_number + 1) >= context.solid_config["work_on_attempt"]:
        return "success"
    else:
        raise RetryRequested(
            max_retries=context.solid_config["max_retries"],
            seconds_to_wait=context.solid_config["delay"],
        )


@pipeline(
    preset_defs=[
        PresetDefinition(
            name="pass_after_retry",
            run_config={
                "solids": {
                    "retry_solid": {
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
    echo(retry_solid())
