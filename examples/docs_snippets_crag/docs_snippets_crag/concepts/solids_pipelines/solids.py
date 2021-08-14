# pylint: disable=unused-argument

import requests
from dagster import DagsterType, InputDefinition, Nothing, Output, OutputDefinition, solid


class MockResponse:
    def json(self):
        return {}


class MockRequest:
    def get(self, _url):
        return MockResponse()


requests = MockRequest()

# start_solid_marker


@solid
def my_solid():
    return "hello"


# end_solid_marker


# start_configured_solid_marker
@solid(config_schema={"api_endpoint": str})
def my_configurable_solid(context):
    api_endpoint = context.solid_config["api_endpoint"]
    data = requests.get(f"{api_endpoint}/data").json()
    return data


# end_configured_solid_marker

# start_input_solid_marker


@solid
def my_input_solid(abc, xyz):
    pass


# end_input_solid_marker


# start_typed_input_solid_marker

MyDagsterType = DagsterType(type_check_fn=lambda _, value: value % 2 == 0, name="MyDagsterType")


@solid(input_defs=[InputDefinition(name="abc", dagster_type=MyDagsterType)])
def my_typed_input_solid(abc):
    pass


# end_typed_input_solid_marker


# start_output_solid_marker


@solid
def my_output_solid():
    return 5


# end_output_solid_marker

# start_multi_output_solid_marker


@solid(
    output_defs=[
        OutputDefinition(name="first_output"),
        OutputDefinition(name="second_output"),
    ],
)
def my_multi_output_solid():
    yield Output(5, output_name="first_output")
    yield Output(6, output_name="second_output")


# end_multi_output_solid_marker

# start_solid_context_marker
@solid(config_schema={"name": str})
def context_solid(context):
    name = context.solid_config["name"]
    context.log.info(f"My name is {name}")


# end_solid_context_marker

# start_solid_factory_pattern_marker
def x_solid(
    arg,
    name="default_name",
    input_defs=None,
    **kwargs,
):
    """
    Args:
        args (any): One or more arguments used to generate the nwe solid
        name (str): The name of the new solid.
        input_defs (list[InputDefinition]): Any input definitions for the new solid. Default: None.

    Returns:
        function: The new solid.
    """

    @solid(name=name, input_defs=input_defs or [InputDefinition("start", Nothing)], **kwargs)
    def _x_solid(context):
        # Solid logic here
        pass

    return _x_solid


# end_solid_factory_pattern_marker
