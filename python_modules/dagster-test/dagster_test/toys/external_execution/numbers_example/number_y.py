import os

from dagster_pipes import open_dagster_pipes

from dagster_test.toys.external_execution.numbers_example.util import (
    compute_data_version,
    store_asset_value,
)

with open_dagster_pipes() as context:
    storage_root = context.get_extra("storage_root")

    value = int(os.environ["NUMBER_Y"])
    store_asset_value("number_y", storage_root, value)

    context.log.info(f"{context.asset_key}: {value} read from $NUMBER_Y environment variable.")
    context.report_asset_materialization(
        metadata={"is_even": value % 2 == 0},
        data_version=compute_data_version(value),
    )
