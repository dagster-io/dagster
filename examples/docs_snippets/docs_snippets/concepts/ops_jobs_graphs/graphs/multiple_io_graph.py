# start_marker
from dagster import OpExecutionContext, graph, op


@op
def return_one(context: OpExecutionContext) -> int:
    return 1


@op
def add_one(context: OpExecutionContext, number: int):
    return number + 1


@op
def adder(context: OpExecutionContext, a: int, b: int) -> int:
    return a + b


@graph
def inputs_and_outputs():
    value = return_one()
    a = add_one(value)
    b = add_one(value)
    adder(a, b)


# end_marker
