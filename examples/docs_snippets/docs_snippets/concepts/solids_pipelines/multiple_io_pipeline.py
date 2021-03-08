# pylint: disable=unused-argument, no-value-for-parameter

# start_marker
from dagster import InputDefinition, Output, OutputDefinition, pipeline, solid


@solid
def return_one(context):
    return 1


@solid(input_defs=[InputDefinition("number", int)])
def add_one(context, number):
    return number + 1


@solid(
    input_defs=[
        InputDefinition(name="a", dagster_type=int),
        InputDefinition(name="b", dagster_type=int),
    ],
    output_defs=[
        OutputDefinition(name="sum", dagster_type=int),
    ],
)
def adder(context, a, b):
    yield Output(a + b, output_name="sum")


@pipeline
def inputs_and_outputs_pipeline():
    value = return_one()
    a = add_one(value)
    b = add_one(value)
    adder(a, b)


# end_marker
