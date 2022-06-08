from unittest import mock

from pandas import DataFrame

from dagster import AssetGroup, AssetsDefinition, ResourceDefinition, graph, op


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
