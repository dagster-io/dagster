import dagster
from dagster import check
from dagster.core.definitions import (Solid, InputDefinition)
from dagster.transform_only_solid import (dep_only_input, no_args_transform_solid)


def _set_key_value(ddict, key, value):
    ddict[key] = value
    return value


def test_execute_solid_with_dep_only_inputs_no_api():
    did_run_dict = {}

    step_one_solid = Solid(
        name='step_one_solid',
        inputs=[],
        transform_fn=lambda: _set_key_value(did_run_dict, 'step_one', True),
        outputs=[],
    )

    only_dep_input = InputDefinition(
        name='step_one_solid',
        input_fn=lambda arg_dict: check.not_implemented('should not get here'),
        argument_def_dict={},
        depends_on=step_one_solid
    )

    step_two_solid = Solid(
        name='step_two_solid',
        inputs=[only_dep_input],
        transform_fn=lambda **kwargs: _set_key_value(did_run_dict, 'step_two', True),
        outputs=[],
    )

    pipeline = dagster.pipeline(solids=[step_one_solid, step_two_solid])

    # from dagster.utils import logging

    pipeline_result = dagster.execute_pipeline(
        dagster.context(),
        # dagster.context(loggers=[logging.define_logger('test')], log_level=logging.INFO),
        pipeline,
        {},
    )

    assert pipeline_result.success

    for result in pipeline_result.result_list:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True


def test_execute_solid_with_dep_only_inputs_with_api():
    did_run_dict = {}

    step_one_solid = no_args_transform_solid(
        name='step_one_solid',
        no_args_transform_fn=lambda: _set_key_value(did_run_dict, 'step_one', True),
    )

    step_two_solid = no_args_transform_solid(
        name='step_two_solid',
        no_args_transform_fn=lambda: _set_key_value(did_run_dict, 'step_two', True),
        inputs=[dep_only_input(step_one_solid)],
    )

    pipeline = dagster.pipeline(solids=[step_one_solid, step_two_solid])

    pipeline_result = dagster.execute_pipeline(dagster.context(), pipeline, {})

    for result in pipeline_result.result_list:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True
