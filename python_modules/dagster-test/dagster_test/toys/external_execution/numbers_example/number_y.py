import os

from dagster_externals import init_dagster_ext

from .util import compute_data_version, store_asset_value

context = init_dagster_ext()
storage_root = context.get_extra("storage_root")

value = int(os.environ["NUMBER_Y"])
store_asset_value("number_y", storage_root, value)

context.log(f"{context.asset_key}: {value} read from $NUMBER_Y environment variable.")
context.report_asset_metadata(context.asset_key, "is_even", value % 2 == 0)
context.report_asset_data_version(context.asset_key, compute_data_version(value))
