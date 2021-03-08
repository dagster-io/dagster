# pylint: disable=unused-argument

import requests
from dagster import InputDefinition, Nothing, Output, OutputDefinition, solid


class MockResponse:
    def json(self):
        return {}


class MockRequest:
    def get(self, _url):
        return MockResponse()


requests = MockRequest()

# start_solid_marker


@solid
def my_solid(context):
    return "hello"


# end_solid_marker


# start_input_definition_marker


# The name is required, but both dagster_type and description are optional.
# - The dagster type will be checked at runtime
# - The description useful for documentation and is displayed in Dagit

InputDefinition(name="abc", dagster_type=str, description="Some description")
InputDefinition(name="xyz", dagster_type=int, description="Some description")


# end_input_definition_marker


# start_configured_solid_marker
@solid(config_schema={"api_endpoint": str})
def my_configured_solid(context):
    api_endpoint = context.solid_config["api_endpoint"]
    data = requests.get(f"{api_endpoint}/data").json()
    return data


# end_configured_solid_marker

# start_input_example_solid_marker

# Inputs abc and xyz must appear in the same order on the compute fn
@solid(
    input_defs=[
        InputDefinition(name="abc", dagster_type=str, description="Some description"),
        InputDefinition(name="xyz", dagster_type=int, description="Some description"),
    ]
)
def my_input_example_solid(context, abc, xyz):
    pass


# end_input_example_solid_marker

# start_typehints_solid_marker
@solid
def my_typehints_solid(context, abc: str, xyz: int):
    pass


# end_typehints_solid_marker


# start_input_output_solid_marker
@solid(
    input_defs=[
        InputDefinition(name="a", dagster_type=int),
        InputDefinition(name="b", dagster_type=int),
    ],
    output_defs=[
        OutputDefinition(name="sum", dagster_type=int),
        OutputDefinition(name="difference", dagster_type=int),
    ],
)
def my_input_output_example_solid(context, a, b):
    yield Output(a + b, output_name="sum")
    yield Output(a - b, output_name="difference")


# end_input_output_solid_marker

# start_solid_context_marker
@solid(config_schema={"name": str})
def context_solid(context):
    name = context.solid_config["name"]
    context.log.info(f"My name is {name}")


# end_solid_context_marker

# start_with_multiple_inputs_marker
@solid(
    input_defs=[
        InputDefinition(name="value_a", dagster_type=int),
        InputDefinition(name="value_b", dagster_type=int),
    ]
)
def adder(context, value_a, value_b):
    context.log.info(str(value_a + value_b))


# end_with_multiple_inputs_marker

# start_with_single_output_marker
@solid(output_defs=[OutputDefinition(name="my_name", dagster_type=str)])
def single_output_solid(_context):
    return "Dagster"


# end_with_single_output_marker

# start_with_multiple_outputs_marker
@solid(
    output_defs=[
        OutputDefinition(name="my_name", dagster_type=str),
        OutputDefinition(name="age", dagster_type=str),
    ]
)
def multiple_outputs_solid(_context):
    yield Output("dagster", output_name="my_name")
    yield Output("dagster", output_name="age")


# end_with_multiple_outputs_marker

# start_with_untyped_marker
@solid(
    input_defs=[
        InputDefinition(name="value_a"),
        InputDefinition(name="value_b"),
    ]
)
def untyped_inputs_solid(context, value_a, value_b):
    context.log.info(str(value_a + value_b))


# end_with_untyped_marker

# start_with_untyped_no_input_defs_marker
@solid
def no_input_defs_solid(context, value_a, value_b):
    context.log.info(str(value_a + value_b))


# end_with_untyped_no_input_defs_marker

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
