# ruff: isort: skip_file
import dagster as dg

from unittest.mock import MagicMock


def create_db_connection():
    return MagicMock()


# start example
import pandas as pd
import dagster as dg
from dagster_slack import SlackResource


@dg.op
def fetch_files_from_slack(slack: SlackResource) -> pd.DataFrame:
    files = slack.get_client().files_list(channel="#random")
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


@dg.op
def store_files(files):
    return files.to_sql(name="slack_files", con=create_db_connection())


@dg.graph_asset
def slack_files_table():
    return store_files(fetch_files_from_slack())


# end example

slack_mock = MagicMock()

store_slack_files = dg.define_asset_job(
    "store_slack_files", selection=dg.AssetSelection.assets(slack_files_table)
)


# start_basic_dependencies
import dagster as dg


@dg.asset
def upstream_asset():
    return 1


@dg.op
def add_one(input_num):
    return input_num + 1


@dg.op
def multiply_by_two(input_num):
    return input_num * 2


@dg.graph_asset
def middle_asset(upstream_asset):
    return multiply_by_two(add_one(upstream_asset))


@dg.asset
def downstream_asset(middle_asset):
    return middle_asset + 7


# end_basic_dependencies

basic_deps_job = dg.define_asset_job(
    "basic_deps_job",
    dg.AssetSelection.assets(upstream_asset, middle_asset, downstream_asset),
)


@dg.op(out={"one": dg.Out(), "two": dg.Out()})
def two_outputs(upstream):
    yield dg.Output(output_name="one", value=upstream)
    yield dg.Output(output_name="two", value=upstream)


# start_basic_dependencies_2
import dagster as dg


@dg.graph_multi_asset(
    outs={"first_asset": dg.AssetOut(), "second_asset": dg.AssetOut()}
)
def two_assets(upstream_asset):
    one, two = two_outputs(upstream_asset)
    return {"first_asset": one, "second_asset": two}


# end_basic_dependencies_2

second_basic_deps_job = dg.define_asset_job(
    "second_basic_deps_job", dg.AssetSelection.assets(upstream_asset, two_assets)
)

# start_explicit_dependencies
import dagster as dg


@dg.graph_multi_asset(outs={"asset_one": dg.AssetOut(), "asset_two": dg.AssetOut()})
def one_and_two(upstream_asset):
    one, two = two_outputs(upstream_asset)
    return {"asset_one": one, "asset_two": two}


# end_explicit_dependencies

explicit_deps_job = dg.define_asset_job(
    "explicit_deps_job", dg.AssetSelection.assets(upstream_asset, one_and_two)
)


defs = dg.Definitions(
    assets=dg.load_assets_from_current_module(),
    jobs=[
        basic_deps_job,
        store_slack_files,
        second_basic_deps_job,
        explicit_deps_job,
    ],
    resources={"slack": slack_mock},
)
