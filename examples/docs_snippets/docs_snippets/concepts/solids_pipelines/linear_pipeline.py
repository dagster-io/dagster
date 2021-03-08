# pylint: disable=unused-argument

# start_marker
from dagster import InputDefinition, pipeline, solid


@solid
def return_one(context):
    return 1


@solid(input_defs=[InputDefinition("number", int)])
def add_one(context, number):
    return number + 1


@pipeline
def linear_pipeline():
    add_one(add_one(add_one(return_one())))


# end_marker
