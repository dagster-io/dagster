from dagster_pipes import open_dagster_pipes

from .util import compute_data_version, load_asset_value, store_asset_value

with open_dagster_pipes() as pipes:
    storage_root = pipes.get_extra("storage_root")
    number_y = load_asset_value("number_y", storage_root)
    number_x = load_asset_value("number_x", storage_root)
    value = number_x + number_y
    store_asset_value("number_sum", storage_root, value)

    pipes.log.info(f"{pipes.asset_key}: {number_x} + {number_y} = {value}")
    pipes.report_asset_materialization(data_version=compute_data_version(value))
