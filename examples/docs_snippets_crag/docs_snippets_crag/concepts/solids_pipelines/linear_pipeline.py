# pylint: disable=unused-argument

# start_marker
from dagster import pipeline, solid


@solid
def return_one(context) -> int:
    return 1


@solid
def add_one(context, number: int) -> int:
    return number + 1


@pipeline
def linear_pipeline():
    add_one(add_one(add_one(return_one())))


# end_marker
