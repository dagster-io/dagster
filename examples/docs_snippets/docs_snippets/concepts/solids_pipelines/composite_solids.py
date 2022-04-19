# isort: skip_file
# pylint: disable=unused-argument
# pylint: disable=print-call

from dagster import graph, job, op
from .unnested_ops import (
    return_fifty,
    add_thirty_two,
    multiply_by_one_point_eight,
    log_number,
)

# start_composite_solid_example_marker


@graph
def celsius_to_fahrenheit(number):
    return add_thirty_two(multiply_by_one_point_eight(number))


@job
def all_together_nested():
    log_number(celsius_to_fahrenheit(return_fifty()))


# end_composite_solid_example_marker

# start_composite_solid_config_marker


@op(config_schema={"n": float})
def add_n(context, number):
    return number + context.op_config["n"]


@op(config_schema={"m": float})
def multiply_by_m(context, number):
    return number * context.op_config["m"]


@graph
def add_n_times_m_graph(number):
    return multiply_by_m(add_n(number))


@job
def subgraph_config_job():
    add_n_times_m_graph(return_fifty())


# end_composite_solid_config_marker

# start_composite_multi_output_marker

from dagster import GraphOut


@op
def echo(i):
    print(i)


@op
def one() -> int:
    return 1


@op
def hello() -> str:
    return "hello"


@graph(out={"x": GraphOut(), "y": GraphOut()})
def graph_with_multiple_outputs():
    x = one()
    y = hello()
    return {"x": x, "y": y}


@job
def subgraph_multiple_outputs_job():
    x, y = graph_with_multiple_outputs()
    echo(x)
    echo(y)


# end_composite_multi_output_marker
