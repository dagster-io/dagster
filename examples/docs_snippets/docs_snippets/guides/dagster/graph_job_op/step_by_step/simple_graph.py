from dagster import graph, solid


@solid
def do_something():
    pass


# start_simple_graph
@graph
def nest_stuff():
    do_something()


# end_simple_graph
