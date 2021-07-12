from dagster import graph, op


@op
def do_something():
    ...


@graph
def do_it_all():
    do_something()
