from dagster import Config, config_mapping, graph, op


class AddNConfig(Config):
    n: float


@op
def add_n(config: AddNConfig, number):
    return number + config.n


class MultiplyByMConfig(Config):
    m: float


@op
def multiply_by_m(config: MultiplyByMConfig, number):
    return number * config.m


class ToFahrenheitConfig(Config):
    from_unit: str


@config_mapping
def generate_config(config_in: ToFahrenheitConfig):
    if config_in.from_unit == "celsius":
        n = 32
    elif config_in.from_unit == "kelvin":
        n = -459.67
    else:
        raise ValueError()

    return {"multiply_by_m": {"config": {"m": 1.8}}, "add_n": {"config": {"n": n}}}


@graph(config=generate_config)
def to_fahrenheit(number):
    return multiply_by_m(add_n(number))
