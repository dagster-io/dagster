import random
from typing import List

import dagster as dg


# Define the asset
@dg.asset
def my_asset(context: dg.AssetExecutionContext):
    context.log.info("Hello, world!")


# Define asset job
my_job = dg.define_asset_job("my_job", selection=[my_asset])


# highlight-start
# Define file check
def check_for_new_files() -> List[str]:
    if random.random() > 0.5:
        return ["file1", "file2"]
    return []


# Define the sensor
@dg.sensor(
    job=my_job,
    minimum_interval_seconds=5,
    default_status=dg.DefaultSensorStatus.RUNNING,  # Sensor is turned on by default
)
def new_file_sensor():
    new_files = check_for_new_files()
    # New files, run `my_job`
    if new_files:
        for filename in new_files:
            yield dg.RunRequest(run_key=filename)
    # No new files, skip the run and log the reason
    else:
        yield dg.SkipReason("No new files found")
        # highlight-end


defs = dg.Definitions(assets=[my_asset], jobs=[my_job], sensors=[new_file_sensor])


if __name__ == "__main__":
    new_file_sensor()
    dg.materialize(
        [my_asset],
    )
