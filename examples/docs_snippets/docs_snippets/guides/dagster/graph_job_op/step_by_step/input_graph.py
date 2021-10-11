from dagster import solid, graph


@solid
def requires_input(x):
    return x + 1


# start_simple_input
@graph
def nests_with_input(x):
    requires_input(x)


# end_simple_input
