from dagster_ext import init_dagster_ext

from .util import compute_data_version, store_asset_value

context = init_dagster_ext()
storage_root = context.get_extra("storage_root")

multiplier = context.get_extra("multiplier")
value = 2 * multiplier
store_asset_value("number_x", storage_root, value)

context.log(f"{context.asset_key}: {2} * {multiplier} = {value}")
context.report_asset_materialization(data_version=compute_data_version(value))
