from dagster import (
    Bool,
    Dict,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    OutputDefinition,
    PresetDefinition,
    ResourceDefinition,
    String,
    execute_pipeline,
    file_relative_path,
    pipeline,
    solid,
)


class ErrorableResource:
    pass


def resource_init(init_context):
    if init_context.resource_config['throw_on_resource_init']:
        raise Exception('throwing from in resource_fn')
    return ErrorableResource()


def define_errorable_resource():
    return ResourceDefinition(
        resource_fn=resource_init, config_field=Field(Dict({'throw_on_resource_init': Field(Bool)}))
    )


solid_throw_config = Field(
    Dict(fields={'throw_in_solid': Field(Bool), 'return_wrong_type': Field(Bool)})
)


@solid(name='emit_num', output_defs=[OutputDefinition(Int)], config_field=solid_throw_config)
def emit_num(context):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    if context.solid_config['return_wrong_type']:
        return 'wow'

    return 13


@solid(
    name='num_to_str',
    input_defs=[InputDefinition('num', Int)],
    output_defs=[OutputDefinition(String)],
    config_field=solid_throw_config,
)
def num_to_str(context, num):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    if context.solid_config['return_wrong_type']:
        return num + num

    return str(num)


@solid(
    name='str_to_num',
    input_defs=[InputDefinition('string', String)],
    output_defs=[OutputDefinition(Int)],
    config_field=solid_throw_config,
)
def str_to_num(context, string):
    if context.solid_config['throw_in_solid']:
        raise Exception('throwing from in the solid')

    if context.solid_config['return_wrong_type']:
        return string + string

    return int(string)


@pipeline(
    mode_defs=[
        ModeDefinition(
            name='errorable_mode', resource_defs={'errorable_resource': define_errorable_resource()}
        )
    ],
    preset_defs=[
        PresetDefinition.from_files(
            'passing',
            environment_files=[file_relative_path(__file__, 'environments/error.yaml')],
            mode='errorable_mode',
        )
    ],
)
def error_monster():
    start = emit_num.alias('start')()
    middle = num_to_str.alias('middle')(num=start)
    str_to_num.alias('end')(string=middle)


if __name__ == '__main__':
    result = execute_pipeline(
        error_monster,
        {
            'solids': {
                'start': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
                'middle': {'config': {'throw_in_solid': False, 'return_wrong_type': True}},
                'end': {'config': {'throw_in_solid': False, 'return_wrong_type': False}},
            },
            'resources': {'errorable_resource': {'config': {'throw_on_resource_init': False}}},
        },
    )
    print('Pipeline Success: ', result.success)
