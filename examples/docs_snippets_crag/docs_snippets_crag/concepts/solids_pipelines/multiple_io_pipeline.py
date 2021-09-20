# pylint: disable=unused-argument, no-value-for-parameter

# start_marker
from dagster import pipeline, solid


@solid
def return_one(context) -> int:
    return 1


@solid
def add_one(context, number: int):
    return number + 1


@solid
def adder(context, a: int, b: int) -> int:
    return a + b


@pipeline
def inputs_and_outputs_pipeline():
    value = return_one()
    a = add_one(value)
    b = add_one(value)
    adder(a, b)


# end_marker
