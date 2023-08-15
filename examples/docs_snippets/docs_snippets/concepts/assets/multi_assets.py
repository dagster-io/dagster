# ruff: isort: skip_file


# start_basic_multi_asset
from dagster import AssetOut, multi_asset


@multi_asset(
    outs={
        "my_string_asset": AssetOut(),
        "my_int_asset": AssetOut(),
    }
)
def my_function():
    return "abc", 123


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
from dagster import AssetOut, Output, multi_asset


@multi_asset(
    outs={
        "a": AssetOut(is_required=False),
        "b": AssetOut(is_required=False),
    },
    can_subset=True,
)
def split_actions(context):
    if "a" in context.selected_output_names:
        yield Output(value=123, output_name="a")
    if "b" in context.selected_output_names:
        yield Output(value=456, output_name="b")


# end_subsettable_multi_asset

# start_asset_deps_multi_asset
from dagster import AssetKey, AssetOut, Output, multi_asset


@multi_asset(
    outs={"c": AssetOut(), "d": AssetOut()},
    internal_asset_deps={
        "c": {AssetKey("a")},
        "d": {AssetKey("b")},
    },
)
def my_complex_assets(a, b):
    # c only depends on a
    yield Output(value=a + 1, output_name="c")
    # d only depends on b
    yield Output(value=b + 1, output_name="d")


# end_asset_deps_multi_asset
