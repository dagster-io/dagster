from dagster import graph, op


@op(config_schema={"n": float})
def add_n(context, number):
    return number + context.op_config["n"]


@op(config_schema={"m": float})
def multiply_by_m(context, number):
    return number * context.op_config["m"]


@graph(config={"multiply_by_m": {"config": {"m": 1.8}}, "add_n": {"config": {"n": 32}}})
def celsius_to_fahrenheit(number):
    return multiply_by_m(add_n(number))
