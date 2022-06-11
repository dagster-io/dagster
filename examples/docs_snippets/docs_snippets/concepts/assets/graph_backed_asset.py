from unittest import mock

from pandas import DataFrame

from dagster import (
    AssetGroup,
    AssetsDefinition,
    ResourceDefinition,
    graph,
    op,
    asset,
    build_assets_job,
    repository,
    GraphOut,
    Out,
    Output,
    AssetKey,
)


def create_db_connection():
    return "yay"


# start example


@op(required_resource_keys={"slack"})
def fetch_files_from_slack(context) -> DataFrame:
    files = context.resources.slack.files_list(channel="#random")
    return DataFrame(
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


@graph
def store_slack_files_in_sql():
    store_files(fetch_files_from_slack())


graph_asset = AssetsDefinition.from_graph(store_slack_files_in_sql)

# end example

slack_mock = mock.MagicMock()

store_slack_files = AssetGroup(
    [graph_asset],
    resource_defs={"slack": ResourceDefinition.hardcoded_resource(slack_mock)},
).build_job("store_slack_files")


@op
def add_one(input_num):
    return input_num + 1


# start_basic_dependencies


@asset
def upstream_asset():
    return 1


@graph
def middle_asset(upstream_asset):
    return add_one(upstream_asset)


middle_asset = AssetsDefinition.from_graph(middle_asset)


@asset
def downstream_asset(middle_asset):
    return middle_asset + 1


# end_basic_dependencies

basic_deps_job = build_assets_job(
    "basic_deps_job", [upstream_asset, middle_asset, downstream_asset]
)


@op(out={"one": Out(), "two": Out()})
def two_outputs(upstream):
    yield Output(output_name="one", value=upstream)
    yield Output(output_name="two", value=upstream)


# start_basic_dependencies_2


@graph(out={"first_asset": GraphOut(), "second_asset": GraphOut()})
def two_assets_graph(upstream_asset):
    one, two = two_outputs(upstream_asset)
    return {"first_asset": one, "second_asset": two}


two_assets = AssetsDefinition.from_graph(two_assets_graph)

# end_basic_dependencies_2

second_basic_deps_job = build_assets_job("second_basic_deps_job", [upstream_asset, two_assets])

# start_explicit_dependencies


@graph(out={"one": GraphOut(), "two": GraphOut()})
def return_one_and_two(zero):
    one, two = two_outputs(zero)
    return {"one": one, "two": two}


explicit_deps_asset = AssetsDefinition.from_graph(
    return_one_and_two,
    asset_keys_by_input_name={"zero": AssetKey("upstream_asset")},
    asset_keys_by_output_name={"one": AssetKey("asset_one"), "two": AssetKey("asset_two")},
)

# end_explicit_dependencies

explicit_deps_job = build_assets_job("explicit_deps_job", [upstream_asset, explicit_deps_asset])


@repository
def my_repo():
    return [basic_deps_job, store_slack_files, second_basic_deps_job, explicit_deps_job]
