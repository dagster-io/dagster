# ruff: isort: skip_file


# start_basic_multi_asset
from dagster import AssetSpec, multi_asset


@multi_asset(specs=[AssetSpec("users"), AssetSpec("orders")])
def my_function():
    # some code that writes out data to the users table and the orders table
    ...


# end_basic_multi_asset

# start_io_manager_multi_asset
from dagster import AssetOut, multi_asset


@multi_asset(
    outs={
        "s3_asset": AssetOut(io_manager_key="s3_io_manager"),
        "adls_asset": AssetOut(io_manager_key="adls2_io_manager"),
    },
)
def my_assets():
    return "store_me_on_s3", "store_me_on_adls2"


# end_io_manager_multi_asset

# start_subsettable_multi_asset
from dagster import AssetExecutionContext, AssetSpec, MaterializeResult, multi_asset


@multi_asset(
    specs=[AssetSpec("asset1", skippable=True), AssetSpec("asset2", skippable=True)],
    can_subset=True,
)
def split_actions(context: AssetExecutionContext):
    if "asset1" in context.op_execution_context.selected_asset_keys:
        yield MaterializeResult(asset_key="asset1")
    if "asset2" in context.op_execution_context.selected_asset_keys:
        yield MaterializeResult(asset_key="asset2")


# end_subsettable_multi_asset

# start_asset_deps_multi_asset
from dagster import AssetKey, AssetSpec, asset, multi_asset


@asset
def a(): ...


@asset
def b(): ...


@multi_asset(specs=[AssetSpec("c", deps=["b"]), AssetSpec("d", deps=["a"])])
def my_complex_assets(): ...


# end_asset_deps_multi_asset
