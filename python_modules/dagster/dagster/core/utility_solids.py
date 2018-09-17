from dagster import (
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
)


def define_stub_solid(name, value):
    check.str_param(name, 'name')

    def _value_t_fn(*_args):
        yield Result(value)

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition()],
        transform_fn=_value_t_fn,
    )
