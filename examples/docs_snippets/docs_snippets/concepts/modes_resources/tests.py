# pylint: disable=unused-argument
from dagster import ModeDefinition, ResourceDefinition, pipeline, solid
from dagster.core.execution.api import execute_pipeline

api_client = ResourceDefinition.mock_resource()


def process(data):
    return data


# start_mode_test_before_marker
@solid
def get_data_without_resource(context):
    dummy_data = [1, 2, 3]
    # Do not call external apis in tests
    # return call_api()
    return dummy_data


# end_mode_test_before_marker

# start_mode_test_after_marker


@solid(required_resource_keys={"api"})
def get_data(context):
    return context.resources.api.call()


@solid
def do_something(context, data):
    output = process(data)
    return output


@pipeline(
    mode_defs=[
        ModeDefinition(name="unit_test", resource_defs={"api": ResourceDefinition.mock_resource()}),
        ModeDefinition(name="prod", resource_defs={"api": api_client}),
    ]
)
def download_pipeline():
    do_something(get_data())


# end_mode_test_after_marker

# start_execution_marker


def test_local():
    result = execute_pipeline(download_pipeline, mode="unit_test")
    assert result.success


def run_in_prod():
    execute_pipeline(download_pipeline, mode="prod")


# end_execution_marker
