from dagster_pipes import open_dagster_pipes

from dagster_test.toys.external_execution.numbers_example.util import (
    compute_data_version,
    store_asset_value,
)

with open_dagster_pipes() as context:
    storage_root = context.get_extra("storage_root")

    multiplier = context.get_extra("multiplier")
    value = 2 * multiplier
    store_asset_value("number_x", storage_root, value)

    context.log.info(f"{context.asset_key}: {2} * {multiplier} = {value}")
    context.report_asset_materialization(
        data_version=compute_data_version(value), metadata={"foo": "bar"}
    )
