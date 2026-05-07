# ruff: isort: skip_file
import dagster as dg

from .unnested_ops import (
    add_thirty_two,
    log_number,
    multiply_by_one_point_eight,
    return_fifty,
)


# start_composite_solid_example_marker
@dg.graph
def celsius_to_fahrenheit(number):
    return add_thirty_two(multiply_by_one_point_eight(number))


@dg.job
def all_together_nested():
    log_number(celsius_to_fahrenheit(return_fifty()))


# end_composite_solid_example_marker


# start_composite_solid_config_marker
@dg.op(config_schema={"n": float})
def add_n(context: dg.OpExecutionContext, number):
    return number + context.op_config["n"]


@dg.op(config_schema={"m": float})
def multiply_by_m(context: dg.OpExecutionContext, number):
    return number * context.op_config["m"]


@dg.graph
def add_n_times_m_graph(number):
    return multiply_by_m(add_n(number))


@dg.job
def subgraph_config_job():
    add_n_times_m_graph(return_fifty())


# end_composite_solid_config_marker

# start_composite_multi_output_marker
import dagster as dg


@dg.op
def echo(i):
    print(i)  # noqa: T201


@dg.op
def one() -> int:
    return 1


@dg.op
def hello() -> str:
    return "hello"


@dg.graph(out={"x": dg.GraphOut(), "y": dg.GraphOut()})
def graph_with_multiple_outputs():
    x = one()
    y = hello()
    return {"x": x, "y": y}


@dg.job
def subgraph_multiple_outputs_job():
    x, y = graph_with_multiple_outputs()
    echo(x)
    echo(y)


# end_composite_multi_output_marker
