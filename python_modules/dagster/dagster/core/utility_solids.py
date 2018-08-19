from dagster import (
    ArgumentDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
    check,
    types,
)


def define_pass_value_solid(name):
    check.str_param(name, 'name')

    def _value_t_fn(_context, _inputs, config_dict):
        yield Result(config_dict['value'])

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition(dagster_type=types.String)],
        config_def={'value': ArgumentDefinition(types.String)},
        transform_fn=_value_t_fn,
    )


def define_pass_mem_value(name, value):
    check.str_param(name, 'name')

    def _value_t_fn(_context, _inputs, _config_dict):
        yield Result(value)

    return SolidDefinition(
        name=name,
        inputs=[],
        outputs=[OutputDefinition()],
        config_def={},
        transform_fn=_value_t_fn,
    )
