from dagster import config_mapping, graph, op


@op(config_schema={"n": float})
def add_n(context, number):
    return number + context.op_config["n"]


@op(config_schema={"m": float})
def multiply_by_m(context, number):
    return number * context.op_config["m"]


@config_mapping(config_schema={"from_unit": str})
def generate_config(val):
    if val["from_unit"] == "celsius":
        n = 32
    elif val["from_unit"] == "kelvin":
        n = -459.67
    else:
        raise ValueError()

    return {"multiply_by_m": {"config": {"m": 1.8}}, "add_n": {"config": {"n": n}}}


@graph(config=generate_config)
def to_fahrenheit(number):
    return multiply_by_m(add_n(number))
