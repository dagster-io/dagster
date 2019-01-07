from collections import defaultdict
from contextlib import contextmanager
import itertools
import os
import tempfile
import uuid

from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    PipelineDefinition,
    SolidInstance,
    check,
    define_stub_solid,
    execute_pipeline,
)

from dagster.core.execution import build_sub_pipeline
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


def _dep_key_of(solid):
    return SolidInstance(solid.definition.name, solid.name)


def build_pipeline_with_input_stubs(pipeline_def, inputs):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(inputs, 'inputs', key_type=str, value_type=dict)

    deps = defaultdict(dict)
    for solid_name, dep_dict in pipeline_def.dependencies.items():
        for input_name, dep in dep_dict.items():
            deps[solid_name][input_name] = dep

    stub_solid_defs = []

    for solid_name, input_dict in inputs.items():
        if not pipeline_def.has_solid(solid_name):
            raise DagsterInvariantViolationError(
                (
                    'You are injecting an input value for solid {solid_name} '
                    'into pipeline {pipeline_name} but that solid was not found'
                ).format(solid_name=solid_name, pipeline_name=pipeline_def.name)
            )

        solid = pipeline_def.solid_named(solid_name)
        for input_name, input_value in input_dict.items():
            stub_solid_def = define_stub_solid(
                '__stub_{solid_name}_{input_name}'.format(
                    solid_name=solid_name, input_name=input_name
                ),
                input_value,
            )
            stub_solid_defs.append(stub_solid_def)
            deps[_dep_key_of(solid)][input_name] = DependencyDefinition(stub_solid_def.name)

    return PipelineDefinition(
        name=pipeline_def.name + '_stubbed',
        solids=pipeline_def.solid_defs + stub_solid_defs,
        context_definitions=pipeline_def.context_definitions,
        dependencies=deps,
    )


def execute_solids(pipeline_def, solid_names, inputs=None, environment=None):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.list_param(solid_names, 'solid_names', of_type=str)
    inputs = check.opt_dict_param(inputs, 'inputs', key_type=str, value_type=dict)
    environment = check.opt_dict_param(environment, 'environment')

    sub_pipeline = build_sub_pipeline(pipeline_def, solid_names)
    stubbed_pipeline = build_pipeline_with_input_stubs(sub_pipeline, inputs)
    result = execute_pipeline(stubbed_pipeline, environment)

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
