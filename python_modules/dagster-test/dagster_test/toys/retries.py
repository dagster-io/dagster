import time

from dagster import PresetDefinition, RetryRequested, lambda_solid, pipeline, solid


@lambda_solid
def echo(x):
    return x


_ATTEMPTS = 0


@solid(config_schema={"max_retries": int, "delay": int, "work_on_attempt": int})
def retry_solid(context):
    time.sleep(1)
    global _ATTEMPTS  # pylint: disable=global-statement
    _ATTEMPTS += 1
    if _ATTEMPTS >= context.solid_config["work_on_attempt"]:
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
                            "delay": 2,
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
