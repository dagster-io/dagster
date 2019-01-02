from collections import defaultdict
from contextlib import contextmanager
import itertools
import os
import tempfile
import uuid

from dagster import (
    DependencyDefinition,
    PipelineDefinition,
    SolidInstance,
    check,
    config,
    define_stub_solid,
    execute_pipeline,
)

from dagster.core.definitions import SolidInputHandle

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


def execute_solids(pipeline_def, solid_names, inputs=None, environment=None):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.list_param(solid_names, 'solid_names', of_type=str)
    inputs = check.opt_dict_param(inputs, 'inputs', key_type=str, value_type=dict)
    environment = check.opt_dict_param(environment, 'environment')

    injected_solids = []
    deps = defaultdict(dict)

    for solid_name in solid_names:
        solid_def = pipeline_def.solid_named(solid_name).definition

        for input_def in solid_def.input_defs:
            input_name = input_def.name
            dep_key = SolidInstance(solid_def.name, solid_name)
            if input_name in inputs.get(solid_name, {}):
                stub_solid = define_stub_solid(
                    '{solid_name}_{input_name}'.format(
                        solid_name=solid_name, input_name=input_name
                    ),
                    inputs[solid_name][input_name],
                )
                injected_solids.append(stub_solid)
                deps[dep_key][input_name] = DependencyDefinition(stub_solid.name)
                continue

            inp_handle = SolidInputHandle(pipeline_def.solid_named(solid_name), input_def)

            if pipeline_def.dependency_structure.has_dep(inp_handle):
                output_handle = pipeline_def.dependency_structure.get_dep(inp_handle)
                deps[dep_key][input_name] = DependencyDefinition(
                    solid=output_handle.solid.name, output=output_handle.output_def.name
                )
                continue

    existing = [pipeline_def.solid_named(solid_name).definition for solid_name in solid_names]

    isolated_pipeline = PipelineDefinition(
        name=pipeline_def.name + '_isolated',
        solids=existing + injected_solids,
        context_definitions=pipeline_def.context_definitions,
        dependencies=deps,
    )

    result = execute_pipeline(isolated_pipeline, environment)

    if not result.success:
        for solid_result in result.result_list:
            if not solid_result.success:
                solid_result.reraise_user_error()

    return {sr.solid.name: sr for sr in result.result_list}


def execute_solid(pipeline_def, solid_name, inputs=None, environment=None):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.str_param(solid_name, 'solid_name')
    inputs = check.opt_dict_param(inputs, 'inputs', key_type=str)
    environment = check.opt_dict_param(environment, 'environment')

    return execute_solids(
        pipeline_def, [solid_name], {solid_name: inputs} if inputs else None, environment
    )[solid_name]
