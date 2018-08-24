from dagster import (
    ArgumentDefinition,
    LibrarySolidDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    execute_pipeline,
    config,
    types,
)


def test_basic_library_solid():
    def get_t_fn(args):
        def _t_fn(*_args, **_kwargs):
            yield Result({args['key']: args['value']})

        return _t_fn

    library_solid_def = LibrarySolidDefinition(
        name='return_value_in_key',
        argument_def_dict={
            'key' : ArgumentDefinition(types.String),
            'value' : ArgumentDefinition(types.String),
        },
        solid_creation_fn=lambda name, args: SolidDefinition(
            name=name,
            inputs=[],
            outputs=[OutputDefinition()],
            transform_fn=get_t_fn(args),
        )
    )

    solid = library_solid_def.create_solid(
        'instance_name', {
            'key': 'some_key',
            'value': 'some_value'
        }
    )

    assert isinstance(solid, SolidDefinition)
    assert solid.name == 'instance_name'

    pipeline = PipelineDefinition(solids=[solid])

    result = execute_pipeline(pipeline, config.Environment())
    assert result.success

    solid_result = result.result_for_solid('instance_name')
    assert solid_result.transformed_value() == {'some_key': 'some_value'}
