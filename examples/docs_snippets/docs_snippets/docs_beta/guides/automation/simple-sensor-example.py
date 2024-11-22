import random
from typing import List

from dagster import (
    AssetExecutionContext,
    Definitions,
    RunRequest,
    SkipReason,
    asset,
    define_asset_job,
    sensor,
)


@asset
def my_asset(context: AssetExecutionContext):
    context.log.info("Hello, world!")


my_job = define_asset_job("my_job", selection=[my_asset])


# highlight-start
def check_for_new_files() -> list[str]:
    if random.random() > 0.5:
        return ["file1", "file2"]
    return []


@sensor(target=my_job, minimum_interval_seconds=5)
def new_file_sensor():
    new_files = check_for_new_files()
    if new_files:
        for filename in new_files:
            yield RunRequest(run_key=filename)
    else:
        yield SkipReason("No new files found")
        # highlight-end


defs = Definitions(assets=[my_asset], jobs=[my_job], sensors=[new_file_sensor])


if __name__ == "__main__":
    from dagster import materialize

    new_file_sensor()
    materialize(
        [my_asset],
    )
