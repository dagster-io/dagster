# isort: skip_file
# pylint: disable=unused-argument,reimported

# start_basic_multi_asset
from dagster import Out, multi_asset


@multi_asset(
    outs={
        "my_string_asset": Out(),
        "my_int_asset": Out(),
    }
)
def my_function():
    return "abc", 123


# end_basic_multi_asset

# start_io_manager_multi_asset
from dagster import Out, multi_asset


@multi_asset(
    outs={
        "s3_asset": Out(io_manager_key="s3_io_manager"),
        "adls_asset": Out(io_manager_key="adls2_io_manager"),
    },
)
def my_assets():
    return "store_me_on_s3", "store_me_on_adls2"


# end_io_manager_multi_asset

# start_subsettable_multi_asset
from dagster import Out, Output, multi_asset


@multi_asset(
    outs={
        "a": Out(is_required=False),
        "b": Out(is_required=False),
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
from dagster import AssetKey, Out, Output, multi_asset


@multi_asset(
    outs={"c": Out(), "d": Out()},
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
