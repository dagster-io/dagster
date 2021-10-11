from dagster import solid, composite_solid


@solid
def do_something():
    pass


# start_simple_composite
@composite_solid
def nest_stuff():
    do_something()


# end_simple_composite
