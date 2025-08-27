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


class ToFahrenheitConfig(dg.Config):
    from_unit: str


@dg.config_mapping
def generate_config(config_in: ToFahrenheitConfig):
    if config_in.from_unit == "celsius":
        n = 32
    elif config_in.from_unit == "kelvin":
        n = -459.67
    else:
        raise ValueError()

    return {"multiply_by_m": {"config": {"m": 1.8}}, "add_n": {"config": {"n": n}}}


@dg.graph(config=generate_config)
def to_fahrenheit(number):
    return multiply_by_m(add_n(number))
