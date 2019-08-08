from dagster import InputDefinition, OutputDefinition, execute_pipeline, pipeline
from dagster.core.test_utils import single_output_solid


def _set_key_value(ddict, key, value):
    ddict[key] = value
    return value


def test_execute_solid_with_dep_only_inputs_no_api():
    did_run_dict = {}

    step_one_solid = single_output_solid(
        name='step_one_solid',
        input_defs=[],
        compute_fn=lambda context, args: _set_key_value(did_run_dict, 'step_one', True),
        output_def=OutputDefinition(),
    )

    step_two_solid = single_output_solid(
        name='step_two_solid',
        input_defs=[InputDefinition('step_one_solid')],
        compute_fn=lambda context, args: _set_key_value(did_run_dict, 'step_two', True),
        output_def=OutputDefinition(),
    )

    @pipeline
    def pipe():
        step_two_solid(step_one_solid())

    pipeline_result = execute_pipeline(pipe)

    assert pipeline_result.success

    for result in pipeline_result.solid_result_list:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True


def test_execute_solid_with_dep_only_inputs_with_api():
    did_run_dict = {}

    step_one_solid = single_output_solid(
        name='step_one_solid',
        input_defs=[],
        compute_fn=lambda context, args: _set_key_value(did_run_dict, 'step_one', True),
        output_def=OutputDefinition(),
    )

    step_two_solid = single_output_solid(
        name='step_two_solid',
        compute_fn=lambda context, args: _set_key_value(did_run_dict, 'step_two', True),
        input_defs=[InputDefinition(step_one_solid.name)],
        output_def=OutputDefinition(),
    )

    @pipeline
    def pipe():
        step_two_solid(step_one_solid())

    pipeline_result = execute_pipeline(pipe)

    for result in pipeline_result.solid_result_list:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True
