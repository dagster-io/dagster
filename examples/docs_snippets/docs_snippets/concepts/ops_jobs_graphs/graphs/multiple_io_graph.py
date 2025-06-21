# start_marker
import dagster as dg


@dg.op
def return_one(context: dg.OpExecutionContext) -> int:
    return 1


@dg.op
def add_one(context: dg.OpExecutionContext, number: int):
    return number + 1


@dg.op
def adder(context: dg.OpExecutionContext, a: int, b: int) -> int:
    return a + b


@dg.graph
def inputs_and_outputs():
    value = return_one()
    a = add_one(value)
    b = add_one(value)
    adder(a, b)


# end_marker
