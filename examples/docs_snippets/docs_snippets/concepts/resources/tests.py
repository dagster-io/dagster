# ruff: isort: skip_file


from dagster import ResourceDefinition

api_client = ResourceDefinition.mock_resource()


def process(data):
    return data


# start_test_before_marker
from dagster import op


@op
def get_data_without_resource():
    dummy_data = [1, 2, 3]
    # Do not call external apis in tests
    # return call_api()
    return dummy_data


# end_test_before_marker

# start_test_after_marker
from dagster import graph, op, ConfigurableResource


class MyApi(ConfigurableResource):
    def call(self):
        ...


@op
def get_data(api: MyApi):
    return api.call()


@op
def do_something(context, data):
    output = process(data)
    return output


@graph
def download():
    do_something(get_data())


# The prod job for the download graph.
download_job = download.to_job(resource_defs={"api": MyApi()})


# end_test_after_marker

# start_execution_marker


def test_local():
    # Since we have access to the computation graph independent of the set of resources, we can
    # test it locally.
    result = download.execute_in_process(
        resources={"api": ResourceDefinition.mock_resource()}
    )
    assert result.success


def run_in_prod():
    download_job.execute_in_process()


# end_execution_marker
