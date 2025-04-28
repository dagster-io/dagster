import os

import dagster as dg

MY_DIRECTORY = "data"


@dg.asset
def my_asset(context: dg.AssetExecutionContext):
    context.log.info("Hello, world!")


my_job = dg.define_asset_job("my_job", selection=[my_asset])


@dg.sensor(
    job=my_job,
    minimum_interval_seconds=5,
    default_status=dg.DefaultSensorStatus.RUNNING,
)
# highlight-start
# Enable sensor context
def updated_file_sensor(context):
    # Get current cursor value from sensor context
    last_mtime = float(context.cursor) if context.cursor else 0
    # highlight-end

    max_mtime = last_mtime

    # Loop through directory
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            # Get the file's last modification time (st_mtime)
            fstats = os.stat(filepath)
            file_mtime = fstats.st_mtime

            # If the file was updated since the last eval time, continue
            if file_mtime <= last_mtime:
                continue

            # Construct the RunRequest with run_key and config
            run_key = f"{filename}:{file_mtime}"
            run_config = {"ops": {"my_asset": {"config": {"filename": filename}}}}
            yield dg.RunRequest(run_key=run_key, run_config=run_config)

            # highlight-start
            # Keep the larger value of max_mtime and file last updated
            max_mtime = max(max_mtime, file_mtime)

    # Update the cursor
    context.update_cursor(str(max_mtime))
    # highlight-end


defs = dg.Definitions(assets=[my_asset], jobs=[my_job], sensors=[updated_file_sensor])
