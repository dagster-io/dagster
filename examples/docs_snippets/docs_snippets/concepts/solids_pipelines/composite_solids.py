# pylint: disable=unused-argument

from dagster import InputDefinition, composite_solid, pipeline, repository, solid


@solid
def my_solid(_):
    pass


@solid
def return_one(context):
    return 1


# start_composite_solid_example_marker
@solid(config_schema={"hi": str}, input_defs=[InputDefinition("number", int)])
def add_one(context, number):
    return number + 1


@solid(input_defs=[InputDefinition("number", int)])
def multiply_by_three(context, number):
    return number * 3


@composite_solid(input_defs=[InputDefinition("number", int)])
def add_one_times_three_solid(number):
    return multiply_by_three(add_one(number))


# end_composite_solid_example_marker

# start_composite_solid_config_marker


@solid(config_schema={"n": int}, input_defs=[InputDefinition("number", int)])
def add_n(context, number):
    return number + context.solid_config["n"]


@solid(config_schema={"m": int}, input_defs=[InputDefinition("number", int)])
def multiply_by_m(context, number):
    return number * context.solid_config["m"]


@composite_solid(input_defs=[InputDefinition("number", int)])
def add_n_times_m_solid(number):
    return multiply_by_m(add_n(number))


# end_composite_solid_config_marker

# start_composite_mapping_marker


def config_mapping_fn(config):
    x = config["x"]
    return {"add_n": {"config": {"n": x}}, "multiply_by_m": {"config": {"m": x}}}


@composite_solid(
    config_fn=config_mapping_fn,
    config_schema={"x": int},
    input_defs=[InputDefinition("number", int)],
)
def add_x_multiply_by_x(number):
    return multiply_by_m(add_n(number))


# end_composite_mapping_marker


@pipeline
def my_pipeline():
    add_one_times_three_solid()


@pipeline
def my_other_pipeline():
    add_n_times_m_solid()


@repository
def my_repository():
    return [my_pipeline, my_other_pipeline]
