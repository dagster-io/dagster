from dagster import graph, op


@op
def do_something():
    pass


@graph
def do_stuff():
    do_something()
