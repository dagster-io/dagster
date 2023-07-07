# ruff: isort: skip_file
from dagster import (
    AssetKey,
    load_assets_from_current_module,
    Out,
    Output,
    AssetSelection,
    define_asset_job,
    Definitions,
)
from mock import MagicMock


def create_db_connection():
    return MagicMock()


# start example
import pandas as pd
from dagster import graph_asset, op


@op(required_resource_keys={"slack"})
def fetch_files_from_slack(context) -> pd.DataFrame:
    files = context.resources.slack.files_list(channel="#random")
    return pd.DataFrame(
        [
            {
                "id": file.get("id"),
                "created": file.get("created"),
                "title": file.get("title"),
                "permalink": file.get("permalink"),
            }
            for file in files
        ]
    )


@op
def store_files(files):
    return files.to_sql(name="slack_files", con=create_db_connection())


@graph_asset
def slack_files_table():
    return store_files(fetch_files_from_slack())


# end example

slack_mock = MagicMock()

store_slack_files = define_asset_job(
    "store_slack_files", selection=AssetSelection.assets(slack_files_table)
)


# start_basic_dependencies
from dagster import asset, graph_asset, op


@asset
def upstream_asset():
    return 1


@op
def add_one(input_num):
    return input_num + 1


@op
def multiply_by_two(input_num):
    return input_num * 2


@graph_asset
def middle_asset(upstream_asset):
    return multiply_by_two(add_one(upstream_asset))


@asset
def downstream_asset(middle_asset):
    return middle_asset + 7


# end_basic_dependencies

basic_deps_job = define_asset_job(
    "basic_deps_job",
    AssetSelection.assets(upstream_asset, middle_asset, downstream_asset),
)


@op(out={"one": Out(), "two": Out()})
def two_outputs(upstream):
    yield Output(output_name="one", value=upstream)
    yield Output(output_name="two", value=upstream)


# start_basic_dependencies_2
from dagster import AssetOut, graph_multi_asset


@graph_multi_asset(outs={"first_asset": AssetOut(), "second_asset": AssetOut()})
def two_assets(upstream_asset):
    one, two = two_outputs(upstream_asset)
    return {"first_asset": one, "second_asset": two}


# end_basic_dependencies_2

second_basic_deps_job = define_asset_job(
    "second_basic_deps_job", AssetSelection.assets(upstream_asset, two_assets)
)

# start_explicit_dependencies
from dagster import AssetOut, graph_multi_asset


@graph_multi_asset(outs={"asset_one": AssetOut(), "asset_two": AssetOut()})
def one_and_two(upstream_asset):
    one, two = two_outputs(upstream_asset)
    return {"asset_one": one, "asset_two": two}


# end_explicit_dependencies

explicit_deps_job = define_asset_job(
    "explicit_deps_job", AssetSelection.assets(upstream_asset, one_and_two)
)


defs = Definitions(
    assets=load_assets_from_current_module(),
    jobs=[
        basic_deps_job,
        store_slack_files,
        second_basic_deps_job,
        explicit_deps_job,
    ],
    resources={"slack": slack_mock},
)
