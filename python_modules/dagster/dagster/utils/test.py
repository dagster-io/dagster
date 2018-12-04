from collections import defaultdict
from contextlib import contextmanager
import itertools
import os
import tempfile
import uuid

from dagster import (
    check,
    PipelineDefinition,
    config,
    define_stub_solid,
    execute_pipeline,
)

from dagster.core.execution_context import RuntimeExecutionContext


def create_test_runtime_execution_context(loggers=None, resources=None):
    run_id = str(uuid.uuid4())
    return RuntimeExecutionContext(run_id, loggers, resources)


def _unlink_swallow_errors(path):
    check.str_param(path, 'path')
    try:
        os.unlink(path)
    except:  # pylint: disable=W0702
        pass


@contextmanager
def get_temp_file_name():
    temp_file_name = tempfile.mkstemp()[1]
    try:
        yield temp_file_name
    finally:
        _unlink_swallow_errors(temp_file_name)


@contextmanager
def get_temp_file_names(number):
    check.int_param(number, 'number')

    temp_file_names = list()
    for _ in itertools.repeat(None, number):
        temp_file_name = tempfile.mkstemp()[1]
        temp_file_names.append(temp_file_name)

    try:
        yield tuple(temp_file_names)
    finally:
        for temp_file_name in temp_file_names:
            _unlink_swallow_errors(temp_file_name)


def execute_solid(
    pipeline_def,
    solid_name,
    inputs=None,
    environment=None,
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.str_param(solid_name, 'solid_name')
    inputs = check.opt_dict_param(inputs, 'inputs', key_type=str)
    environment = check.opt_inst_param(environment, 'environment', (dict, config.Environment))

    injected_solids = defaultdict(dict)

    for input_name, input_value in inputs.items():
        injected_solids[solid_name][input_name] = define_stub_solid(
            '{solid_name}_{input_name}'.format(
                solid_name=solid_name,
                input_name=input_name,
            ),
            input_value,
        )

    single_solid_pipeline = PipelineDefinition.create_single_solid_pipeline(
        pipeline_def,
        solid_name,
        injected_solids,
    )

    result = execute_pipeline(single_solid_pipeline, environment)

    solid_result = result.result_for_solid(solid_name)

    if not solid_result.success:
        solid_result.reraise_user_error()

    return solid_result
