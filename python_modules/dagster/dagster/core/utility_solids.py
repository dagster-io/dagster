from dagster import (
    ArgumentDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
)


def define_stub_solid(name, value):
    check.str_param(name, 'name')

    def _value_t_fn(_context, _inputs, _config_dict):
        yield Result(value)

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition()],
        transform_fn=_value_t_fn,
    )
