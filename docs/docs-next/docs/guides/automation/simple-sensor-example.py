from typing import List

from dagster import AssetExecutionContext, Definitions, RunRequest, asset, define_asset_job, sensor


@asset
def my_asset(context: AssetExecutionContext):
    context.log.info("Hello, world!")


my_job = define_asset_job("my_job", selection=[my_asset])


def check_for_new_files() -> List[str]:
    return ["file1", "file2"]


@sensor(target=my_job)
def new_file_sensor():
    new_files = check_for_new_files()
    for filename in new_files:
        yield RunRequest(run_key=filename)


defs = Definitions(assets=[my_asset], jobs=[my_job], sensors=[new_file_sensor])


if __name__ == "__main__":
    from dagster import materialize

    new_file_sensor()
    materialize(
        [my_asset],
    )
