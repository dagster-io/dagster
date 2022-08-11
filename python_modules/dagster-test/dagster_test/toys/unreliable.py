from random import random

from dagster import Field, graph, op

DEFAULT_EXCEPTION_RATE = 0.3


@op
def unreliable_start():
    return 1


@op(config_schema={"rate": Field(float, is_required=False, default_value=DEFAULT_EXCEPTION_RATE)})
def unreliable_op(context, num):
    if random() < context.op_config["rate"]:
        raise Exception("blah")

    return num


@graph
def unreliable():
    one = unreliable_op.alias("one")
    two = unreliable_op.alias("two")
    three = unreliable_op.alias("three")
    four = unreliable_op.alias("four")
    five = unreliable_op.alias("five")
    six = unreliable_op.alias("six")
    seven = unreliable_op.alias("seven")
    seven(six(five(four(three(two(one(unreliable_start())))))))


unreliable_job = unreliable.to_job(
    name="unreliable_job_no_schedule",
    description="Demo graph of chained ops that fail with a configurable probability.",
)
