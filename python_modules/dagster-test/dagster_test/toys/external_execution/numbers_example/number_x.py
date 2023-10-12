from dagster_pipes import open_dagster_pipes

from .util import compute_data_version, store_asset_value

with open_dagster_pipes() as pipes:
    storage_root = pipes.get_extra("storage_root")

    multiplier = pipes.get_extra("multiplier")
    value = 2 * multiplier
    store_asset_value("number_x", storage_root, value)

    pipes.log.info(f"{pipes.asset_key}: {2} * {multiplier} = {value}")
    pipes.report_asset_materialization(data_version=compute_data_version(value))
