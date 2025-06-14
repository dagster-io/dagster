# start_marker
import dagster as dg


@dg.op
def return_one(context: dg.OpExecutionContext) -> int:
    return 1


@dg.op
def add_one(context: dg.OpExecutionContext, number: int) -> int:
    return number + 1


@dg.graph
def linear():
    add_one(add_one(add_one(return_one())))


# end_marker
