import os
import time

from dagster import pipeline, repository
from dagster.legacy import solid


# start_loop_marker_0
@solid(config_schema={"file_path": str})
def wait_for_condition_met(context):
    while True:
        file_path = context.solid_config["file_path"]
        if os.path.exists(file_path):
            context.log.info("Condition is met.")
            break
        context.log.info("Condition not met. Check again soon.")
        time.sleep(1)

    context.log.info("Hello, the computation is completed.")


@pipeline
def user_in_the_loop_pipeline():
    wait_for_condition_met()


# end_loop_marker_0


@repository
def my_repo():
    return [user_in_the_loop_pipeline]
