import dagster
from dagster import check
from dagster.core.definitions import (Solid, InputDefinition)


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

    results = dagster.execute_pipeline(
        dagster.context(),
        # dagster.context(loggers=[logging.define_logger('test')], log_level=logging.INFO),
        pipeline,
        {},
        throw_on_error=True
    )

    for result in results:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True


def dep_only_input(solid):
    return InputDefinition(
        name=solid.name,
        input_fn=lambda **kwargs: check.not_implemented('should not get here'),
        argument_def_dict={},
        depends_on=solid,
    )


def no_args_transfom_solid(name, no_args_transform, inputs=None):
    # check arguments
    # transform should not take args?

    return Solid(
        name=name,
        inputs=inputs or [],
        transform_fn=lambda **kwargs: no_args_transform(),
        outputs=[],
    )


def test_execute_solid_with_dep_only_inputs_with_api():
    did_run_dict = {}

    step_one_solid = no_args_transfom_solid(
        name='step_one_solid',
        no_args_transform=lambda: _set_key_value(did_run_dict, 'step_one', True),
    )

    step_two_solid = no_args_transfom_solid(
        name='step_two_solid',
        no_args_transform=lambda: _set_key_value(did_run_dict, 'step_two', True),
        inputs=[dep_only_input(step_one_solid)],
    )

    pipeline = dagster.pipeline(solids=[step_one_solid, step_two_solid])

    results = dagster.execute_pipeline(dagster.context(), pipeline, {}, throw_on_error=True)

    for result in results:
        assert result.success

    assert did_run_dict['step_one'] is True
    assert did_run_dict['step_two'] is True
