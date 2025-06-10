# ruff: isort: skip_file


import dagster as dg


@dg.op
def my_op():
    pass


# start_graph_one
@dg.op
def return_one(context: dg.OpExecutionContext):
    return 1


@dg.op
def add_one(context: dg.OpExecutionContext, number: int):
    return number + 1


@dg.graph
def one_plus_one():
    add_one(return_one())


# end_graph_two


# start_multiple_usage_graph
@dg.graph
def multiple_usage():
    add_one(add_one(return_one()))


# end_multiple_usage_graph


# start_alias_graph
@dg.graph
def alias():
    add_one.alias("second_addition")(add_one(return_one()))


# end_alias_graph
