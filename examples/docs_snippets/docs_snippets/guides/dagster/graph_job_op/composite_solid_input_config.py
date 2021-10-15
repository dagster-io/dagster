from dagster import InputDefinition, composite_solid, solid


@solid(input_defs=[InputDefinition("x", dagster_type=int)])
def my_solid(x):
    return x + 1


@solid(input_defs=[InputDefinition("x", dagster_type=int)])
def other_solid(x):
    return x + 1


@composite_solid(input_defs=[InputDefinition("feeds_x", dagster_type=int)])
def my_composite(feeds_x):
    my_solid(feeds_x)
    other_solid(feeds_x)