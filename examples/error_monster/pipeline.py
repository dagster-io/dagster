from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    Bool,
    String,
    Dict,
    OutputDefinition,
    PipelineDefinition,
    SolidInstance,
    RunConfig,
    execute_pipeline,
    solid,
)


@solid(
    name='start',
    outputs=[OutputDefinition(Int)],
    config_field=Field(Dict(fields={'throw_in_solid': Field(Bool)})),
)
def emit_num(context):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    return 13


@solid(
    name='middle',
    inputs=[InputDefinition('num', Int)],
    outputs=[OutputDefinition(String)],
    config_field=Field(Dict(fields={'throw_in_solid': Field(Bool)})),
)
def num_to_str(context, num):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    return str(num)


@solid(
    name='end',
    inputs=[InputDefinition('string', String)],
    outputs=[OutputDefinition(Int)],
    config_field=Field(Dict(fields={'throw_in_solid': Field(Bool)})),
)
def str_to_num(context, string):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    return int(string)


def define_pipeline():
    return PipelineDefinition(
        name="error_monster",
        solids=[emit_num, num_to_str, str_to_num],
        dependencies={
            SolidInstance('start'): {},
            SolidInstance('middle'): {'num': DependencyDefinition('start')},
            SolidInstance('end'): {'string': DependencyDefinition('middle')},
        },
    )


if __name__ == '__main__':
    result = execute_pipeline(
        define_pipeline(),
        {
            'solids': {
                'start': {'config': {'throw_in_solid': True}},
                'middle': {'config': {'throw_in_solid': False}},
                'end': {'config': {'throw_in_solid': False}},
            }
        },
        RunConfig.nonthrowing_in_process(),
    )
    print('Pipeline Success: ', result.success)
