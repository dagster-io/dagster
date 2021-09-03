from random import random

from dagster import Field, graph, op

DEFAULT_EXCEPTION_RATE = 0.3


@op
def unreliable_start():
    return 1


@op(config_schema={"rate": Field(float, is_required=False, default_value=DEFAULT_EXCEPTION_RATE)})
def unreliable(context, num):
    if random() < context.op_config["rate"]:
        raise Exception("blah")

    return num


@graph
def unreliable():
    one = unreliable.alias("one")
    two = unreliable.alias("two")
    three = unreliable.alias("three")
    four = unreliable.alias("four")
    five = unreliable.alias("five")
    six = unreliable.alias("six")
    seven = unreliable.alias("seven")
    seven(six(five(four(three(two(one(unreliable_start())))))))


unreliable_job = unreliable.to_job(
    description="Demo graph of chained ops that fail with a configurable probability."
)
