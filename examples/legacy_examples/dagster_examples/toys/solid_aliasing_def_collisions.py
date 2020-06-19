from dagster import InputDefinition, OutputDefinition, composite_solid, pipeline, solid


@solid
def return_something(_):
    return 'kdjfkjd'


@solid(
    input_defs=[InputDefinition('input_one', str)],
    output_defs=[OutputDefinition(dagster_type=str, name='output_one')],
)
def solid_def_one(_, input_one):
    return input_one


@solid(
    input_defs=[InputDefinition('input_two', str)],
    output_defs=[OutputDefinition(dagster_type=str, name='output_two')],
)
def solid_def_two(_, input_two):
    return input_two


@composite_solid
def order_one():
    solid_def_two.alias('second')(solid_def_one.alias('first')(return_something()))


@composite_solid
def order_two():
    solid_def_one.alias('second')(solid_def_two.alias('first')(return_something()))
    order_one()


@pipeline
def solid_aliasing_def_collisions():
    order_one()
    order_two()
