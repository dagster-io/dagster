from dagster import op, graph


@op
def do_something():
    pass


@graph
def do_stuff():
    do_something()
