from copy import deepcopy
import requests
import io
import pandas
from dagster import (
    ModeDefinition,
    execute_pipeline,
    pipeline,
    resource,
    solid,
)


# start_resources_marker_0
class MockRequester:
    def get_content(self, url):
        pass


@resource
def mock_requester():
    return MockRequester()


# end_resources_marker_0


class Requester:
    def get_content(self, url):
        response = requests.get(url)
        return response.content


@solid(required_resource_keys={"requester"})
def download_cereals(context):
    content = context.resources.requester.get_content(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
    )
    return pandas.read_csv(io.BytesIO(content))


# start_resources_marker_1
@solid(required_resource_keys={"warehouse"})
def normalize_calories(context, cereals):
    columns_to_normalize = [
        "calories",
        "protein",
        "fat",
        "sodium",
        "fiber",
        "carbo",
        "sugars",
        "potass",
        "vitamins",
        "weight",
    ]
    quantities = [cereal["cups"] for cereal in cereals]
    reweights = [1.0 / float(quantity) for quantity in quantities]

    normalized_cereals = deepcopy(cereals)
    for idx in range(len(normalized_cereals)):
        cereal = normalized_cereals[idx]
        for column in columns_to_normalize:
            cereal[column] = float(cereal[column]) * reweights[idx]

    context.resources.warehouse.update_normalized_cereals(normalized_cereals)


# end_resources_marker_1

# start_resources_marker_2
@pipeline(
    mode_defs=[ModeDefinition(resource_defs={"requester": mock_requester})]
)
def resources_pipeline():
    normalize_calories(download_cereals())


# end_resources_marker_2


if __name__ == "__main__":
    result = execute_pipeline(resources_pipeline)
    assert result.success
