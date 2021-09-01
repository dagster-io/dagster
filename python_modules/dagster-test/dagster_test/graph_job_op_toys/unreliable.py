from random import random

from dagster import Field, pipeline, solid

DEFAULT_EXCEPTION_RATE = 0.3


@solid
def unreliable_start(_):
    return 1


@solid(
    config_schema={"rate": Field(float, is_required=False, default_value=DEFAULT_EXCEPTION_RATE)}
)
def unreliable(context, num):
    if random() < context.solid_config["rate"]:
        raise Exception("blah")

    return num


@pipeline(description="Demo pipeline of chained solids that fail with a configurable probability.")
def unreliable_pipeline():
    one = unreliable.alias("one")
    two = unreliable.alias("two")
    three = unreliable.alias("three")
    four = unreliable.alias("four")
    five = unreliable.alias("five")
    six = unreliable.alias("six")
    seven = unreliable.alias("seven")
    seven(six(five(four(three(two(one(unreliable_start())))))))
