from dagster import check

from .definitions import (
    InputDefinition,
    OutputDefinition,
    Result,
    SolidDefinition,
)

from .types import DagsterType


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


def define_serialization_solid(name, dagster_type):
    check.str_param(name, 'name')
    check.inst_param(dagster_type, 'dagster_type', DagsterType)

    def _value_t_fn(info, inputs):
        value = inputs['value']

        with info.context.system_resources.scratch_fs.writeable_file() as ff:
            pass

        yield Result(value)

    return SolidDefinition(
        name=name,
        inputs=[InputDefinition('value', dagster_type)],
        outputs=[OutputDefinition(dagster_type)],
        transform_fn=_value_t_fn,
    )
