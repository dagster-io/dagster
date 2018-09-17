from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    SolidDefinition,
    config,
    execute_pipeline,
)

from dagster.core.test_utils import single_output_transform


def _set_key_value(ddict, key, value):
    ddict[key] = value
    return value


def test_execute_solid_with_dep_only_inputs_no_api():
    did_run_dict = {}

    step_one_solid = single_output_transform(
        name='step_one_solid',
        inputs=[],
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'step_one', True),
        output=OutputDefinition(),
    )

    step_two_solid = single_output_transform(
        name='step_two_solid',
        inputs=[InputDefinition('step_one_solid')],
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'step_two', True),
        output=OutputDefinition(),
    )

    pipeline = PipelineDefinition(
        solids=[step_one_solid, step_two_solid],
        dependencies={
            'step_two_solid': {
                'step_one_solid': DependencyDefinition('step_one_solid')
            },
        },
    )

    # from dagster.utils import logging

    pipeline_result = execute_pipeline(pipeline)

    assert pipeline_result.success

    for result in pipeline_result.result_list:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True


def test_execute_solid_with_dep_only_inputs_with_api():
    did_run_dict = {}

    step_one_solid = single_output_transform(
        name='step_one_solid',
        inputs=[],
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'step_one', True),
        output=OutputDefinition(),
    )

    step_two_solid = single_output_transform(
        name='step_two_solid',
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'step_two', True),
        inputs=[InputDefinition(step_one_solid.name)],
        output=OutputDefinition(),
    )

    pipeline = PipelineDefinition(
        solids=[step_one_solid, step_two_solid],
        dependencies={
            'step_two_solid': {
                step_one_solid.name: DependencyDefinition(step_one_solid.name)
            }
        },
    )

    pipeline_result = execute_pipeline(pipeline)

    for result in pipeline_result.result_list:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True
