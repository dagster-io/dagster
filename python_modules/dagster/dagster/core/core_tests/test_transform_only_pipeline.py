import dagster
from dagster import check
from dagster import config
from dagster.core.definitions import SolidDefinition
from dagster.utils.compatability import create_custom_source_input


def _set_key_value(ddict, key, value):
    ddict[key] = value
    return value


def test_execute_solid_with_dep_only_inputs_no_api():
    did_run_dict = {}

    step_one_solid = SolidDefinition(
        name='step_one_solid',
        inputs=[],
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'step_one', True),
        output=dagster.OutputDefinition(),
    )

    only_dep_input = create_custom_source_input(
        name='step_one_solid',
        source_fn=lambda arg_dict: check.not_implemented('should not get here'),
        argument_def_dict={},
        depends_on=step_one_solid
    )

    step_two_solid = SolidDefinition(
        name='step_two_solid',
        inputs=[only_dep_input],
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'step_two', True),
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(solids=[step_one_solid, step_two_solid])

    # from dagster.utils import logging

    pipeline_result = dagster.execute_pipeline(pipeline, environment=config.Environment.empty())

    assert pipeline_result.success

    for result in pipeline_result.result_list:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True


def test_execute_solid_with_dep_only_inputs_with_api():
    did_run_dict = {}

    step_one_solid = SolidDefinition(
        name='step_one_solid',
        inputs=[],
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'step_one', True),
        output=dagster.OutputDefinition(),
    )

    step_two_solid = SolidDefinition(
        name='step_two_solid',
        transform_fn=lambda context, args: _set_key_value(did_run_dict, 'step_two', True),
        inputs=[dagster.InputDefinition(step_one_solid.name, depends_on=step_one_solid)],
        output=dagster.OutputDefinition(),
    )

    pipeline = dagster.PipelineDefinition(solids=[step_one_solid, step_two_solid])

    pipeline_result = dagster.execute_pipeline(pipeline, environment=config.Environment.empty())

    for result in pipeline_result.result_list:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True
