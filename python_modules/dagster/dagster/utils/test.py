import logging
import uuid

from collections import defaultdict
from contextlib import contextmanager

# top-level include is dangerous in terms of incurring circular deps
from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    ModeDefinition,
    PipelineDefinition,
    SolidDefinition,
    SolidInvocation,
    SystemStorageData,
    check,
    execute_pipeline,
    lambda_solid,
)
from dagster.core.definitions.logger import LoggerDefinition
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.execution.api import RunConfig, scoped_pipeline_context
from dagster.core.execution.context_creation_pipeline import (
    create_log_manager,
    construct_pipeline_execution_context,
    create_context_creation_data,
)
from dagster.core.utility_solids import define_stub_solid
from dagster.core.storage.intermediates_manager import InMemoryIntermediatesManager
from dagster.core.storage.file_manager import LocalFileManager
from dagster.core.storage.runs import InMemoryRunStorage

# pylint: disable=unused-import
from .temp_file import (
    get_temp_file_handle,
    get_temp_file_handle_with_data,
    get_temp_file_name,
    get_temp_file_name_with_data,
    get_temp_file_names,
)


def create_test_pipeline_execution_context(
    logger_defs=None, scoped_resources_builder=None, tags=None, run_config_loggers=None
):
    run_id = str(uuid.uuid4())
    loggers = check.opt_dict_param(
        logger_defs, 'logger_defs', key_type=str, value_type=LoggerDefinition
    )
    mode_def = ModeDefinition(logger_defs=loggers)
    pipeline_def = PipelineDefinition(
        name='test_legacy_context', solid_defs=[], mode_defs=[mode_def]
    )
    run_config_loggers = check.opt_list_param(
        run_config_loggers, 'run_config_loggers', of_type=logging.Logger
    )
    run_config = RunConfig(run_id, tags=tags, loggers=run_config_loggers)
    environment_dict = {'loggers': {key: {} for key in loggers}}
    creation_data = create_context_creation_data(pipeline_def, environment_dict, run_config)
    log_manager = create_log_manager(creation_data)

    scoped_resources_builder = check.opt_inst_param(
        scoped_resources_builder,
        'scoped_resources_builder',
        ScopedResourcesBuilder,
        default=ScopedResourcesBuilder(),
    )
    return construct_pipeline_execution_context(
        context_creation_data=creation_data,
        scoped_resources_builder=scoped_resources_builder,
        system_storage_data=SystemStorageData(
            run_storage=InMemoryRunStorage(),
            intermediates_manager=InMemoryIntermediatesManager(),
            file_manager=LocalFileManager.for_run_id(run_id),
        ),
        log_manager=log_manager,
    )


def _dep_key_of(solid):
    return SolidInvocation(solid.definition.name, solid.name)


def build_pipeline_with_input_stubs(pipeline_def, inputs):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.dict_param(inputs, 'inputs', key_type=str, value_type=dict)

    deps = defaultdict(dict)
    for solid_name, dep_dict in pipeline_def.dependencies.items():
        for input_name, dep in dep_dict.items():
            deps[solid_name][input_name] = dep

    stub_solid_defs = []

    for solid_name, input_dict in inputs.items():
        if not pipeline_def.has_solid_named(solid_name):
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
        solid_defs=pipeline_def.solid_defs + stub_solid_defs,
        mode_defs=pipeline_def.mode_definitions,
        dependencies=deps,
    )


def execute_solids_within_pipeline(
    pipeline_def, solid_names, inputs=None, environment_dict=None, run_config=None
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.list_param(solid_names, 'solid_names', of_type=str)
    inputs = check.opt_dict_param(inputs, 'inputs', key_type=str, value_type=dict)
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict')
    run_config = check.opt_inst_param(run_config, 'run_config', RunConfig)

    sub_pipeline = pipeline_def.build_sub_pipeline(solid_names)
    stubbed_pipeline = build_pipeline_with_input_stubs(sub_pipeline, inputs)
    result = execute_pipeline(stubbed_pipeline, environment_dict, run_config)

    return {sr.solid.name: sr for sr in result.solid_result_list}


def execute_solid_within_pipeline(
    pipeline_def, solid_name, inputs=None, environment_dict=None, run_config=None
):
    check.inst_param(pipeline_def, 'pipeline_def', PipelineDefinition)
    check.str_param(solid_name, 'solid_name')
    inputs = check.opt_dict_param(inputs, 'inputs', key_type=str)
    environment_dict = check.opt_dict_param(environment_dict, 'environment')
    run_config = check.opt_inst_param(run_config, 'run_config', RunConfig)

    return execute_solids_within_pipeline(
        pipeline_def,
        [solid_name],
        {solid_name: inputs} if inputs else None,
        environment_dict,
        run_config,
    )[solid_name]


@contextmanager
def yield_empty_pipeline_context(run_id=None):
    with scoped_pipeline_context(PipelineDefinition([]), {}, RunConfig(run_id=run_id)) as context:
        yield context


def execute_solid(
    solid_def, mode_def=None, input_values=None, environment_dict=None, run_config=None
):
    '''
    Independently execute an individual solid without having to specify a pipeline. This
    also allows one to directly pass in in-memory input values. This is very
    useful for unit test cases.

    '''
    check.inst_param(solid_def, 'solid_def', SolidDefinition)
    check.opt_inst_param(mode_def, 'mode_def', ModeDefinition)
    input_values = check.opt_dict_param(input_values, 'input_values', key_type=str)

    solid_defs = [solid_def]

    def create_value_solid(input_name, input_value):
        @lambda_solid(name=input_name)
        def input_solid():
            return input_value

        return input_solid

    dependencies = defaultdict(dict)

    for input_name, input_value in input_values.items():
        dependencies[solid_def.name][input_name] = DependencyDefinition(input_name)
        solid_defs.append(create_value_solid(input_name, input_value))

    return execute_pipeline(
        PipelineDefinition(
            name='emphemeral_{}_solid_pipeline'.format(solid_def.name),
            solid_defs=solid_defs,
            dependencies=dependencies,
            mode_defs=[mode_def] if mode_def else None,
        ),
        environment_dict=environment_dict,
        run_config=run_config,
    ).result_for_solid(solid_def.name)
