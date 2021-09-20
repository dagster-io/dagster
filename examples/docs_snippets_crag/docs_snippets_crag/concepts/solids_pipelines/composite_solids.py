"""isort:skip_file"""
# pylint: disable=unused-argument
# pylint: disable=print-call

# start_composite_solid_example_marker
from dagster import InputDefinition, composite_solid, pipeline, solid


@solid
def return_one():
    return 1


@solid
def add_one(number: int):
    return number + 1


@solid
def multiply_by_three(number: int):
    return number * 3


@composite_solid(input_defs=[InputDefinition("number", int)])
def add_one_times_three_solid(number):
    return multiply_by_three(add_one(number))


@pipeline
def my_pipeline():
    add_one_times_three_solid(return_one())


# end_composite_solid_example_marker

# start_composite_solid_config_marker


@solid(config_schema={"n": int})
def add_n(context, number: int):
    return number + context.solid_config["n"]


@solid(config_schema={"m": int})
def multiply_by_m(context, number: int):
    return number * context.solid_config["m"]


@composite_solid(input_defs=[InputDefinition("number", int)])
def add_n_times_m_solid(number):
    return multiply_by_m(add_n(number))


# end_composite_solid_config_marker


@pipeline
def my_pipeline_composite_config():
    add_n_times_m_solid()


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


@pipeline
def my_pipeline_config_mapping():
    add_x_multiply_by_x(return_one())


# end_composite_mapping_marker

# start_composite_multi_output_marker

from dagster import OutputDefinition


@solid
def echo(i):
    print(i)


@solid
def one() -> int:
    return 1


@solid
def hello() -> str:
    return "hello"


@composite_solid(output_defs=[OutputDefinition(int, "x"), OutputDefinition(str, "y")])
def composite_multi_outputs():
    x = one()
    y = hello()
    return {"x": x, "y": y}


@pipeline
def my_pipeline_multi_outputs():
    x, y = composite_multi_outputs()
    echo(x)
    echo(y)


# end_composite_multi_output_marker
