import dagster

from dagster import (
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
    SolidDefinition,
    String,
    check,
    execute_pipeline,
    types,
)

from dagster.core.test_utils import single_output_transform

SingleValueDict = Dict({'value': Field(String)})


def define_pass_value_solid(name, description=None):
    check.str_param(name, 'name')
    check.opt_str_param(description, 'description')

    def _value_t_fn(context, _inputs):
        yield Result(context.solid_config['value'])

    return SolidDefinition(
        name=name,
        description=description,
        inputs=[],
        outputs=[OutputDefinition(types.String)],
        config_field=Field(SingleValueDict),
        transform_fn=_value_t_fn,
    )


def test_execute_solid_with_input_same_name():
    a_thing_solid = single_output_transform(
        'a_thing',
        inputs=[InputDefinition(name='a_thing')],
        transform_fn=lambda context, inputs: inputs['a_thing'] + inputs['a_thing'],
        output=dagster.OutputDefinition(),
    )

    pipeline = PipelineDefinition(
        solids=[define_pass_value_solid('pass_value'), a_thing_solid],
        dependencies={'a_thing': {'a_thing': DependencyDefinition('pass_value')}},
    )

    result = execute_pipeline(
        pipeline, environment_dict={'solids': {'pass_value': {'config': {'value': 'foo'}}}}
    )

    assert result.result_for_solid('a_thing').transformed_value() == 'foofoo'


def test_execute_two_solids_with_same_input_name():
    input_def = InputDefinition(name='a_thing')

    solid_one = single_output_transform(
        'solid_one',
        inputs=[input_def],
        transform_fn=lambda context, inputs: inputs['a_thing'] + inputs['a_thing'],
        output=dagster.OutputDefinition(),
    )

    solid_two = single_output_transform(
        'solid_two',
        inputs=[input_def],
        transform_fn=lambda context, inputs: inputs['a_thing'] + inputs['a_thing'],
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(
        solids=[
            define_pass_value_solid('pass_to_one'),
            define_pass_value_solid('pass_to_two'),
            solid_one,
            solid_two,
        ],
        dependencies={
            'solid_one': {'a_thing': DependencyDefinition('pass_to_one')},
            'solid_two': {'a_thing': DependencyDefinition('pass_to_two')},
        },
    )

    result = execute_pipeline(
        pipeline,
        environment_dict={
            'solids': {
                'pass_to_one': {'config': {'value': 'foo'}},
                'pass_to_two': {'config': {'value': 'bar'}},
            }
        },
    )

    assert result.success

    assert result.result_for_solid('solid_one').transformed_value() == 'foofoo'
    assert result.result_for_solid('solid_two').transformed_value() == 'barbar'


def test_execute_dep_solid_different_input_name():
    pass_to_first = define_pass_value_solid('pass_to_first')

    first_solid = single_output_transform(
        'first_solid',
        inputs=[InputDefinition(name='a_thing')],
        transform_fn=lambda context, inputs: inputs['a_thing'] + inputs['a_thing'],
        output=dagster.OutputDefinition(),
    )

    second_solid = single_output_transform(
        'second_solid',
        inputs=[InputDefinition(name='an_input')],
        transform_fn=lambda context, inputs: inputs['an_input'] + inputs['an_input'],
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(
        solids=[pass_to_first, first_solid, second_solid],
        dependencies={
            'first_solid': {'a_thing': DependencyDefinition('pass_to_first')},
            'second_solid': {'an_input': DependencyDefinition('first_solid')},
        },
    )

    result = dagster.execute_pipeline(
        pipeline, environment_dict={'solids': {'pass_to_first': {'config': {'value': 'bar'}}}}
    )

    assert result.success
    assert len(result.solid_result_list) == 3
    assert result.result_for_solid('pass_to_first').transformed_value() == 'bar'
    assert result.result_for_solid('first_solid').transformed_value() == 'barbar'
    assert result.result_for_solid('second_solid').transformed_value() == 'barbarbarbar'
