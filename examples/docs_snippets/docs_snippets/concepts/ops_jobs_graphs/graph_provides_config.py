import dagster as dg


class AddNConfig(dg.Config):
    n: float


@dg.op
def add_n(config: AddNConfig, number):
    return number + config.n


class MultiplyByMConfig(dg.Config):
    m: float


@dg.op
def multiply_by_m(config: MultiplyByMConfig, number):
    return number * config.m


@dg.graph(
    config={"multiply_by_m": {"config": {"m": 1.8}}, "add_n": {"config": {"n": 32}}}
)
def celsius_to_fahrenheit(number):
    return multiply_by_m(add_n(number))
