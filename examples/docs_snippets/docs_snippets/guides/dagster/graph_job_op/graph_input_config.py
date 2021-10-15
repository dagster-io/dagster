from dagster import InputDefinition, graph, solid, GraphIn


@solid(input_defs=[InputDefinition("x", dagster_type=int)])
def my_solid(x):
    return x + 1


@solid(input_defs=[InputDefinition("x", dagster_type=int)])
def other_solid(x):
    return x + 1


@graph(ins={"feeds_x": GraphIn()})
def my_composite(feeds_x):
    my_solid(feeds_x)
    other_solid(feeds_x)
