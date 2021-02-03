import os
import shutil
import tempfile
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
    TypeCheck,
    check,
    execute_pipeline,
    lambda_solid,
)
from dagster.core.definitions.logger import LoggerDefinition
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.definitions.solid import NodeDefinition
from dagster.core.execution.api import create_execution_plan, scoped_pipeline_context
from dagster.core.execution.context_creation_pipeline import (
    SystemPipelineExecutionContext,
    construct_execution_context_data,
    create_context_creation_data,
    create_executor,
    create_log_manager,
)
from dagster.core.instance import DagsterInstance
from dagster.core.scheduler import Scheduler
from dagster.core.scheduler.scheduler import DagsterScheduleDoesNotExist, DagsterSchedulerError
from dagster.core.snap import snapshot_from_execution_plan
from dagster.core.storage.file_manager import LocalFileManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.types.dagster_type import resolve_dagster_type
from dagster.core.utility_solids import define_stub_solid
from dagster.core.utils import make_new_run_id
from dagster.serdes import ConfigurableClass

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
    from dagster.core.storage.intermediate_storage import build_in_mem_intermediates_storage

    loggers = check.opt_dict_param(
        logger_defs, "logger_defs", key_type=str, value_type=LoggerDefinition
    )
    mode_def = ModeDefinition(logger_defs=loggers)
    pipeline_def = PipelineDefinition(
        name="test_legacy_context", solid_defs=[], mode_defs=[mode_def]
    )
    run_config = {"loggers": {key: {} for key in loggers}}
    pipeline_run = PipelineRun(pipeline_name="test_legacy_context", run_config=run_config)
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline=pipeline_def, run_config=run_config)
    creation_data = create_context_creation_data(execution_plan, run_config, pipeline_run, instance)
    log_manager = create_log_manager(creation_data)
    scoped_resources_builder = ScopedResourcesBuilder()
    executor = create_executor(creation_data)

    return SystemPipelineExecutionContext(
        construct_execution_context_data(
            context_creation_data=creation_data,
            scoped_resources_builder=scoped_resources_builder,
            intermediate_storage=build_in_mem_intermediates_storage(pipeline_run.run_id),
            log_manager=log_manager,
            retries=executor.retries,
            raise_on_error=True,
        ),
        executor=executor,
        log_manager=log_manager,
    )


def _dep_key_of(solid):
    return SolidInvocation(solid.definition.name, solid.name)


def build_pipeline_with_input_stubs(pipeline_def, inputs):
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.dict_param(inputs, "inputs", key_type=str, value_type=dict)

    deps = defaultdict(dict)
    for solid_name, dep_dict in pipeline_def.dependencies.items():
        for input_name, dep in dep_dict.items():
            deps[solid_name][input_name] = dep

    stub_solid_defs = []

    for solid_name, input_dict in inputs.items():
        if not pipeline_def.has_solid_named(solid_name):
            raise DagsterInvariantViolationError(
                (
                    "You are injecting an input value for solid {solid_name} "
                    "into pipeline {pipeline_name} but that solid was not found"
                ).format(solid_name=solid_name, pipeline_name=pipeline_def.name)
            )

        solid = pipeline_def.solid_named(solid_name)
        for input_name, input_value in input_dict.items():
            stub_solid_def = define_stub_solid(
                "__stub_{solid_name}_{input_name}".format(
                    solid_name=solid_name, input_name=input_name
                ),
                input_value,
            )
            stub_solid_defs.append(stub_solid_def)
            deps[_dep_key_of(solid)][input_name] = DependencyDefinition(stub_solid_def.name)

    return PipelineDefinition(
        name=pipeline_def.name + "_stubbed",
        solid_defs=pipeline_def.top_level_solid_defs + stub_solid_defs,
        mode_defs=pipeline_def.mode_definitions,
        dependencies=deps,
    )


def execute_solids_within_pipeline(
    pipeline_def,
    solid_names,
    inputs=None,
    run_config=None,
    mode=None,
    preset=None,
    tags=None,
    instance=None,
):
    """Execute a set of solids within an existing pipeline.

    Intended to support tests. Input values may be passed directly.

    Args:
        pipeline_def (PipelineDefinition): The pipeline within which to execute the solid.
        solid_names (FrozenSet[str]): A set of the solid names, or the aliased solids, to execute.
        inputs (Optional[Dict[str, Dict[str, Any]]]): A dict keyed on solid names, whose values are
            dicts of input names to input values, used to pass input values to the solids directly.
            You may also use the ``run_config`` to configure any inputs that are configurable.
        run_config (Optional[dict]): The environment configuration that parameterized this
            execution, as a dict.
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.

    Returns:
        Dict[str, Union[CompositeSolidExecutionResult, SolidExecutionResult]]: The results of
        executing the solids, keyed by solid name.
    """
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.set_param(solid_names, "solid_names", of_type=str)
    inputs = check.opt_dict_param(inputs, "inputs", key_type=str, value_type=dict)

    sub_pipeline = pipeline_def.get_pipeline_subset_def(solid_names)
    stubbed_pipeline = build_pipeline_with_input_stubs(sub_pipeline, inputs)
    result = execute_pipeline(
        stubbed_pipeline,
        run_config=run_config,
        mode=mode,
        preset=preset,
        tags=tags,
        instance=instance,
    )

    return {sr.solid.name: sr for sr in result.solid_result_list}


def execute_solid_within_pipeline(
    pipeline_def,
    solid_name,
    inputs=None,
    run_config=None,
    mode=None,
    preset=None,
    tags=None,
    instance=None,
):
    """Execute a single solid within an existing pipeline.

    Intended to support tests. Input values may be passed directly.

    Args:
        pipeline_def (PipelineDefinition): The pipeline within which to execute the solid.
        solid_name (str): The name of the solid, or the aliased solid, to execute.
        inputs (Optional[Dict[str, Any]]): A dict of input names to input values, used to
            pass input values to the solid directly. You may also use the ``run_config`` to
            configure any inputs that are configurable.
        run_config (Optional[dict]): The environment configuration that parameterized this
            execution, as a dict.
        mode (Optional[str]): The name of the pipeline mode to use. You may not set both ``mode``
            and ``preset``.
        preset (Optional[str]): The name of the pipeline preset to use. You may not set both
            ``mode`` and ``preset``.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        instance (Optional[DagsterInstance]): The instance to execute against. If this is ``None``,
            an ephemeral instance will be used, and no artifacts will be persisted from the run.

    Returns:
        Union[CompositeSolidExecutionResult, SolidExecutionResult]: The result of executing the
        solid.
    """

    return execute_solids_within_pipeline(
        pipeline_def,
        solid_names={solid_name},
        inputs={solid_name: inputs} if inputs else None,
        run_config=run_config,
        mode=mode,
        preset=preset,
        tags=tags,
        instance=instance,
    )[solid_name]


@contextmanager
def yield_empty_pipeline_context(run_id=None, instance=None):
    pipeline = InMemoryPipeline(PipelineDefinition([]))
    pipeline_def = pipeline.get_definition()
    instance = check.opt_inst_param(
        instance, "instance", DagsterInstance, default=DagsterInstance.ephemeral()
    )

    execution_plan = create_execution_plan(pipeline)

    pipeline_run = instance.create_run(
        pipeline_name="<empty>",
        run_id=run_id,
        run_config=None,
        mode=None,
        solids_to_execute=None,
        step_keys_to_execute=None,
        status=None,
        tags=None,
        root_run_id=None,
        parent_run_id=None,
        pipeline_snapshot=pipeline_def.get_pipeline_snapshot(),
        execution_plan_snapshot=snapshot_from_execution_plan(
            execution_plan, pipeline_def.get_pipeline_snapshot_id()
        ),
        parent_pipeline_snapshot=pipeline_def.get_parent_pipeline_snapshot(),
    )
    with scoped_pipeline_context(execution_plan, {}, pipeline_run, instance) as context:
        yield context


def execute_solid(
    solid_def,
    mode_def=None,
    input_values=None,
    tags=None,
    run_config=None,
    raise_on_error=True,
):
    """Execute a single solid in an ephemeral pipeline.

    Intended to support unit tests. Input values may be passed directly, and no pipeline need be
    specified -- an ephemeral pipeline will be constructed.

    Args:
        solid_def (SolidDefinition): The solid to execute.
        mode_def (Optional[ModeDefinition]): The mode within which to execute the solid. Use this
            if, e.g., custom resources, loggers, or executors are desired.
        input_values (Optional[Dict[str, Any]]): A dict of input names to input values, used to
            pass inputs to the solid directly. You may also use the ``run_config`` to
            configure any inputs that are configurable.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        run_config (Optional[dict]): The environment configuration that parameterized this
            execution, as a dict.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``True``, since this is the most useful behavior in test.

    Returns:
        Union[CompositeSolidExecutionResult, SolidExecutionResult]: The result of executing the
        solid.
    """
    check.inst_param(solid_def, "solid_def", NodeDefinition)
    check.opt_inst_param(mode_def, "mode_def", ModeDefinition)
    input_values = check.opt_dict_param(input_values, "input_values", key_type=str)
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
            name="ephemeral_{}_solid_pipeline".format(solid_def.name),
            solid_defs=solid_defs,
            dependencies=dependencies,
            mode_defs=[mode_def] if mode_def else None,
        ),
        run_config=run_config,
        mode=mode_def.name if mode_def else None,
        tags=tags,
        raise_on_error=raise_on_error,
    )
    return result.result_for_handle(solid_def.name)


def check_dagster_type(dagster_type, value):
    """Test a custom Dagster type.

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
    """

    if is_typing_type(dagster_type):
        raise DagsterInvariantViolationError(
            (
                "Must pass in a type from dagster module. You passed {dagster_type} "
                "which is part of python's typing module."
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
                "Type checks can only return TypeCheck. Type {type_name} returned {value}.".format(
                    type_name=dagster_type.display_name, value=repr(type_check)
                )
            )
        return type_check


@contextmanager
def copy_directory(src):
    with tempfile.TemporaryDirectory() as temp_dir:
        dst = os.path.join(temp_dir, os.path.basename(src))
        shutil.copytree(src, dst)
        yield dst


class FilesystemTestScheduler(Scheduler, ConfigurableClass):
    """This class is used in dagster core and dagster_graphql to test the scheduler's interactions
    with schedule storage, which are implemented in the methods defined on the base Scheduler class.
    Therefore, the following methods used to actually schedule jobs (e.g. create and remove cron jobs
    on a cron tab) are left unimplemented.
    """

    def __init__(self, artifacts_dir, inst_data=None):
        check.str_param(artifacts_dir, "artifacts_dir")
        self._artifacts_dir = artifacts_dir
        self._inst_data = inst_data

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": str}

    @staticmethod
    def from_config_value(inst_data, config_value):
        return FilesystemTestScheduler(artifacts_dir=config_value["base_dir"], inst_data=inst_data)

    def debug_info(self):
        return ""

    def start_schedule(self, instance, external_schedule):
        pass

    def stop_schedule(self, instance, schedule_origin_id):
        pass

    def running_schedule_count(self, instance, schedule_origin_id):
        return 0

    def get_logs_path(self, _instance, schedule_origin_id):
        check.str_param(schedule_origin_id, "schedule_origin_id")
        return os.path.join(self._artifacts_dir, "logs", schedule_origin_id, "scheduler.log")

    def wipe(self, instance):
        pass
