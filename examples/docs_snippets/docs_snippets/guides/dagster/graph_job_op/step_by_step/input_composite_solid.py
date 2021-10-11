from dagster import solid, composite_solid


@solid
def requires_input(x):
    return x + 1


requires_input_1 = requires_input.alias("requires_input_1")
requires_input_2 = requires_input.alias("requires_input_2")


# start_simple_input
@composite_solid
def nests_with_input(x):
    requires_input_1(x)
    requires_input_2(x)


# end_simple_input
