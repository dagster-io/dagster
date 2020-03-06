import os
import shutil
import uuid
from collections import defaultdict
from contextlib import contextmanager

# top-level include is dangerous in terms of incurring circular deps
from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    Failure,
    ModeDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    SolidInvocation,
    SystemStorageData,
    TypeCheck,
    check,
    execute_pipeline,
    lambda_solid,
    seven,
)
from dagster.core.definitions.logger import LoggerDefinition
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.definitions.solid import ISolidDefinition
from dagster.core.execution.api import RunConfig, create_execution_plan, scoped_pipeline_context
from dagster.core.execution.context_creation_pipeline import (
    construct_pipeline_execution_context,
    create_context_creation_data,
    create_executor_config,
    create_log_manager,
)
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import ScheduleStatus, Scheduler
from dagster.core.storage.file_manager import LocalFileManager
from dagster.core.storage.intermediates_manager import InMemoryIntermediatesManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.types.dagster_type import resolve_dagster_type
from dagster.core.utility_solids import define_stub_solid
from dagster.core.utils import make_new_run_id

# pylint: disable=unused-import
from ..temp_file import (
    get_temp_dir,
    get_temp_file_handle,
    get_temp_file_handle_with_data,
    get_temp_file_name,
    get_temp_file_name_with_data,
    get_temp_file_names,
)
from ..typing_api import is_typing_type


def create_test_pipeline_execution_context(logger_defs=None):
    run_id = make_new_run_id()
    loggers = check.opt_dict_param(
        logger_defs, 'logger_defs', key_type=str, value_type=LoggerDefinition
    )
    mode_def = ModeDefinition(logger_defs=loggers)
    pipeline_def = PipelineDefinition(
        name='test_legacy_context', solid_defs=[], mode_defs=[mode_def]
    )
    environment_dict = {'loggers': {key: {} for key in loggers}}
    pipeline_run = PipelineRun.create_empty_run('test_legacy_context', run_id, environment_dict)
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline_def, environment_dict, pipeline_run)
    creation_data = create_context_creation_data(
        pipeline_def, environment_dict, pipeline_run, instance, execution_plan
    )
    log_manager = create_log_manager(creation_data)
    scoped_resources_builder = ScopedResourcesBuilder()
    executor_config = create_executor_config(creation_data)
    return construct_pipeline_execution_context(
        context_creation_data=creation_data,
        scoped_resources_builder=scoped_resources_builder,
        system_storage_data=SystemStorageData(
            intermediates_manager=InMemoryIntermediatesManager(),
            file_manager=LocalFileManager.for_instance(instance, run_id),
        ),
        log_manager=log_manager,
        executor_config=executor_config,
        raise_on_error=True,
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
        solid_defs=pipeline_def.top_level_solid_defs + stub_solid_defs,
        mode_defs=pipeline_def.mode_definitions,
        dependencies=deps,
    )


def execute_solids_within_pipeline(
    pipeline_def, solid_names, inputs=None, environment_dict=None, run_config=None
):
    '''Execute a set of solids within an existing pipeline.

    Intended to support tests. Input values may be passed directly.

    Args:
        pipeline_def (PipelineDefinition): The pipeline within which to execute the solid.
        solid_name (str): The name of the solid, or the aliased solid, to execute.
        inputs (Optional[Dict[str, Dict[str, Any]]]): A dict keyed on solid names, whose values are
            dicts of input names to input values, used to pass input values to the solids directly.
            You may also use the ``environment_dict`` to configure any inputs that are configurable.
        environment_dict (Optional[dict]): The enviroment configuration that parameterizes this
            execution, as a dict.
        run_config (Optional[RunConfig]): Optionally specifies additional config options for
            pipeline execution.

    Returns:
        Dict[str, Union[CompositeSolidExecutionResult, SolidExecutionResult]]: The results of
        executing the solids, keyed by solid name.
    '''
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
    '''Execute a single solid within an existing pipeline.

    Intended to support tests. Input values may be passed directly.

    Args:
        pipeline_def (PipelineDefinition): The pipeline within which to execute the solid.
        solid_name (str): The name of the solid, or the aliased solid, to execute.
        inputs (Optional[Dict[str, Any]]): A dict of input names to input values, used to
            pass input values to the solid directly. You may also use the ``environment_dict`` to
            configure any inputs that are configurable.
        environment_dict (Optional[dict]): The enviroment configuration that parameterizes this
            execution, as a dict.
        run_config (Optional[RunConfig]): Optionally specifies additional config options for
            pipeline execution.

    Returns:
        Union[CompositeSolidExecutionResult, SolidExecutionResult]: The result of executing the
        solid.
    '''
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
def yield_empty_pipeline_context(run_id=None, instance=None):
    pipeline = PipelineDefinition([])
    with scoped_pipeline_context(
        pipeline,
        {},
        PipelineRun.create_empty_run('empty', run_id=run_id if run_id is not None else 'TESTING',),
        instance or DagsterInstance.ephemeral(),
        create_execution_plan(pipeline),
    ) as context:
        yield context


def execute_solid(
    solid_def,
    mode_def=None,
    input_values=None,
    environment_dict=None,
    run_config=None,
    raise_on_error=True,
):
    '''Execute a single solid in an ephemeral pipeline.

    Intended to support unit tests. Input values may be passed directly, and no pipeline need be
    specified -- an ephemeral pipeline will be constructed.

    Args:
        solid_def (SolidDefinition): The solid to execute.
        mode_def (Optional[ModeDefinition]): The mode within which to execute the solid. Use this
            if, e.g., custom resources, loggers, or executors are desired.
        input_values (Optional[Dict[str, Any]]): A dict of input names to input values, used to
            pass inputs to the solid directly. You may also use the ``environment_dict`` to
            configure any inputs that are configurable.
        environment_dict (Optional[dict]): The enviroment configuration that parameterizes this
            execution, as a dict.
        run_config (Optional[RunConfig]): Optionally specifies additional config options for
            pipeline execution.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``True``, since this is the most useful behavior in test.

    Returns:
        Union[CompositeSolidExecutionResult, SolidExecutionResult]: The result of executing the
        solid.
    '''
    check.inst_param(solid_def, 'solid_def', ISolidDefinition)
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

    result = execute_pipeline(
        PipelineDefinition(
            name='ephemeral_{}_solid_pipeline'.format(solid_def.name),
            solid_defs=solid_defs,
            dependencies=dependencies,
            mode_defs=[mode_def] if mode_def else None,
        ),
        environment_dict=environment_dict,
        run_config=run_config,
        raise_on_error=raise_on_error,
    )
    return result.result_for_handle(solid_def.name)


def check_dagster_type(dagster_type, value):
    '''Test a custom Dagster type.

    Args:
        dagster_type (Any): The Dagster type to test. Should be one of the
            :ref:`built-in types <builtin>`, a dagster type explicitly constructed with
            :py:func:`as_dagster_type`, :py:func:`@usable_as_dagster_type <dagster_type>`, or
            :py:func:`PythonObjectDagsterType`, or a Python type.
        value (Any): The runtime value to test.

    Returns:
        TypeCheck: The result of the type check.


    Examples:

        .. code-block:: python

            assert check_dagster_type(Dict[Any, Any], {'foo': 'bar'}).success
    '''

    if is_typing_type(dagster_type):
        raise DagsterInvariantViolationError(
            (
                'Must pass in a type from dagster module. You passed {dagster_type} '
                'which is part of python\'s typing module.'
            ).format(dagster_type=dagster_type)
        )

    dagster_type = resolve_dagster_type(dagster_type)
    with yield_empty_pipeline_context() as pipeline_context:
        context = pipeline_context.for_type(dagster_type)
        try:
            type_check = dagster_type.type_check(context, value)
        except Failure as failure:
            return TypeCheck(success=False, description=failure.description)

        if not isinstance(type_check, TypeCheck):
            raise DagsterInvariantViolationError(
                'Type checks can only return TypeCheck. Type {type_name} returned {value}.'.format(
                    type_name=dagster_type.name, value=repr(type_check)
                )
            )
        return type_check


@contextmanager
def restore_directory(src):
    with seven.TemporaryDirectory() as temp_dir:
        dst = os.path.join(temp_dir, os.path.basename(src))
        shutil.copytree(src, dst)
        try:
            yield
        finally:
            shutil.rmtree(src)
            shutil.copytree(dst, src)


class FilesytemTestScheduler(Scheduler):
    def __init__(self, artifacts_dir):
        check.str_param(artifacts_dir, 'artifacts_dir')
        self._artifacts_dir = artifacts_dir

    def start_schedule(self, instance, repository, schedule_name):
        schedule = instance.get_schedule_by_name(repository, schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to start schedule {name}, but it does not exist.'.format(
                    name=schedule_name
                )
            )

        if schedule.status == ScheduleStatus.RUNNING:
            raise DagsterInvariantViolationError(
                'You have attempted to start schedule {name}, but it is already running'.format(
                    name=schedule_name
                )
            )

        started_schedule = schedule.with_status(ScheduleStatus.RUNNING)
        instance.update_schedule(repository, started_schedule)
        return schedule

    def stop_schedule(self, instance, repository, schedule_name):
        schedule = instance.get_schedule_by_name(repository, schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to stop schedule {name}, but was never initialized.'
                'Use `schedule up` to initialize schedules'.format(name=schedule_name)
            )

        if schedule.status == ScheduleStatus.STOPPED:
            raise DagsterInvariantViolationError(
                'You have attempted to stop schedule {name}, but it is already stopped'.format(
                    name=schedule_name
                )
            )

        stopped_schedule = schedule.with_status(ScheduleStatus.STOPPED)
        instance.update_schedule(repository, stopped_schedule)
        return stopped_schedule

    def end_schedule(self, instance, repository, schedule_name):
        schedule = instance.get_schedule_by_name(repository, schedule_name)
        if not schedule:
            raise DagsterInvariantViolationError(
                'You have attempted to end schedule {name}, but it is not running.'.format(
                    name=schedule_name
                )
            )

        instance.storage.delete_schedule(repository, schedule)
        return schedule

    def get_log_path(self, instance, repository, schedule_name):
        check.inst_param(repository, 'repository', RepositoryDefinition)
        check.str_param(schedule_name, 'schedule_name')
        return os.path.join(
            self._artifacts_dir, repository.name, 'logs', '{}'.format(schedule_name)
        )

    def wipe(self, instance):
        pass
