import os
import shutil
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from typing import TYPE_CHECKING, AbstractSet, Any, Dict, Mapping, Optional, Union, cast

# top-level include is dangerous in terms of incurring circular deps
from dagster import (
    DagsterInvariantViolationError,
    DependencyDefinition,
    NodeInvocation,
    _check as check,
)
from dagster._core.definitions import (
    GraphDefinition,
    InputMapping,
    ModeDefinition,
    OpDefinition,
    OutputMapping,
    PipelineDefinition,
)
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.definitions.resource_definition import ScopedResourcesBuilder
from dagster._core.execution.api import create_execution_plan, execute_pipeline
from dagster._core.execution.context.system import PlanExecutionContext
from dagster._core.execution.context_creation_pipeline import (
    create_context_creation_data,
    create_execution_data,
    create_executor,
    create_log_manager,
    create_plan_data,
)
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler import Scheduler
from dagster._core.storage.pipeline_run import DagsterRun
from dagster._core.utility_solids import create_stub_op
from dagster._serdes import ConfigurableClass

# re-export
from ..temp_file import (
    get_temp_dir as get_temp_dir,
    get_temp_file_handle as get_temp_file_handle,
    get_temp_file_handle_with_data as get_temp_file_handle_with_data,
    get_temp_file_name as get_temp_file_name,
    get_temp_file_name_with_data as get_temp_file_name_with_data,
    get_temp_file_names as get_temp_file_names,
)

if TYPE_CHECKING:
    from dagster._core.execution.results import CompositeSolidExecutionResult, OpExecutionResult


def create_test_pipeline_execution_context(
    logger_defs: Optional[Mapping[str, LoggerDefinition]] = None
) -> PlanExecutionContext:
    loggers = check.opt_mapping_param(
        logger_defs, "logger_defs", key_type=str, value_type=LoggerDefinition
    )
    mode_def = ModeDefinition(logger_defs=loggers)
    pipeline_def = PipelineDefinition(
        name="test_legacy_context", node_defs=[], mode_defs=[mode_def]
    )
    run_config: Dict[str, Dict[str, Dict]] = {"loggers": {key: {} for key in loggers}}
    pipeline_run = DagsterRun(pipeline_name="test_legacy_context", run_config=run_config)
    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline=pipeline_def, run_config=run_config)
    creation_data = create_context_creation_data(
        InMemoryPipeline(pipeline_def),
        execution_plan,
        run_config,
        pipeline_run,
        instance,
    )
    log_manager = create_log_manager(creation_data)
    scoped_resources_builder = ScopedResourcesBuilder()
    executor = create_executor(creation_data)

    return PlanExecutionContext(
        plan_data=create_plan_data(creation_data, True, executor.retries),
        execution_data=create_execution_data(
            context_creation_data=creation_data,
            scoped_resources_builder=scoped_resources_builder,
        ),
        log_manager=log_manager,
        output_capture=None,
    )


def _dep_key_of(solid):
    return NodeInvocation(solid.definition.name, solid.name)


def build_pipeline_with_input_stubs(
    pipeline_def: PipelineDefinition, inputs: Mapping[str, Mapping[str, object]]
) -> PipelineDefinition:
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    check.mapping_param(inputs, "inputs", key_type=str, value_type=dict)

    deps: Dict[str, Dict[str, object]] = defaultdict(dict)
    for solid_name, dep_dict in pipeline_def.dependencies.items():
        for input_name, dep in dep_dict.items():
            deps[solid_name][input_name] = dep  # type: ignore

    stub_solid_defs = []

    for solid_name, input_dict in inputs.items():
        if not pipeline_def.has_node_named(solid_name):
            raise DagsterInvariantViolationError(
                (
                    "You are injecting an input value for solid {solid_name} "
                    "into pipeline {pipeline_name} but that solid was not found"
                ).format(solid_name=solid_name, pipeline_name=pipeline_def.name)
            )

        solid = pipeline_def.get_node_named(solid_name)
        for input_name, input_value in input_dict.items():
            stub_solid_def = create_stub_op(
                "__stub_{solid_name}_{input_name}".format(
                    solid_name=solid_name, input_name=input_name
                ),
                input_value,
            )
            stub_solid_defs.append(stub_solid_def)
            deps[_dep_key_of(solid)][input_name] = DependencyDefinition(stub_solid_def.name)

    return PipelineDefinition(
        name=pipeline_def.name + "_stubbed",
        node_defs=[*pipeline_def.top_level_node_defs, *stub_solid_defs],
        mode_defs=pipeline_def.mode_definitions,
        dependencies=deps,  # type: ignore
    )


def execute_solids_within_pipeline(
    pipeline_def: PipelineDefinition,
    solid_names: AbstractSet[str],
    inputs: Optional[Mapping[str, Mapping[str, object]]] = None,
    run_config: Optional[Mapping[str, object]] = None,
    mode: Optional[str] = None,
    preset: Optional[str] = None,
    tags: Optional[Mapping[str, str]] = None,
    instance: Optional[DagsterInstance] = None,
) -> Mapping[str, Union["CompositeSolidExecutionResult", "OpExecutionResult"]]:
    """Execute a set of solids within an existing pipeline.

    Intended to support tests. Input values may be passed directly.

    Args:
        pipeline_def (PipelineDefinition): The pipeline within which to execute the solid.
        solid_names (FrozenSet[str]): A set of the solid names, or the aliased solids, to execute.
        inputs (Optional[Dict[str, Dict[str, Any]]]): A dict keyed on solid names, whose values are
            dicts of input names to input values, used to pass input values to the solids directly.
            You may also use the ``run_config`` to configure any inputs that are configurable.
        run_config (Optional[dict]): The configuration that parameterized this
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
    inputs = check.opt_mapping_param(inputs, "inputs", key_type=str, value_type=dict)

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

    return {sr.node.name: sr for sr in result.node_result_list}


def wrap_op_in_graph(
    op_def: OpDefinition,
    tags: Optional[Mapping[str, Any]] = None,
    do_input_mapping: bool = True,
    do_output_mapping: bool = True,
) -> GraphDefinition:
    """Wraps op in a graph with the same inputs/outputs as the original op."""
    check.opt_mapping_param(tags, "tags", key_type=str)

    if do_input_mapping:
        input_mappings = []
        for input_name in op_def.ins.keys():
            # create an input mapping to the inner node with the same name.
            input_mappings.append(
                InputMapping(
                    graph_input_name=input_name,
                    mapped_node_name=op_def.name,
                    mapped_node_input_name=input_name,
                )
            )
    else:
        input_mappings = None

    if do_output_mapping:
        output_mappings = []
        for output_name in op_def.outs.keys():
            out = op_def.outs[output_name]
            output_mappings.append(
                OutputMapping(
                    graph_output_name=output_name,
                    mapped_node_name=op_def.name,
                    mapped_node_output_name=output_name,
                    from_dynamic_mapping=out.is_dynamic,
                )
            )
    else:
        output_mappings = None

    return GraphDefinition(
        name=f"wraps_{op_def.name}",
        node_defs=[op_def],
        input_mappings=input_mappings,
        output_mappings=output_mappings,
        tags=tags,
    )


def wrap_op_in_graph_and_execute(
    op_def: OpDefinition,
    resources: Optional[Mapping[str, Any]] = None,
    input_values: Optional[Mapping[str, Any]] = None,
    tags: Optional[Mapping[str, Any]] = None,
    run_config: Optional[Mapping[str, object]] = None,
    raise_on_error: bool = True,
    do_input_mapping: bool = True,
    do_output_mapping: bool = True,
    logger_defs: Optional[Mapping[str, LoggerDefinition]] = None,
) -> ExecuteInProcessResult:
    """Execute a single op in an ephemeral, in-process job.

    Intended to support unit tests. Input values may be passed directly, and no job need be
    specified -- an ephemeral one will be constructed.

    Args:
        op_def (OpDefinition): The op to execute.
        resources (Mapping[str, Any]): Resources that will be passed to `execute_in_process`.
        input_values (Optional[Dict[str, Any]]): A dict of input names to input values, used to
            pass inputs to the solid directly. You may also use the ``run_config`` to
            configure any inputs that are configurable.
        tags (Optional[Dict[str, Any]]): Arbitrary key-value pairs that will be added to pipeline
            logs.
        run_config (Optional[dict]): The configuration that parameterized this
            execution, as a dict.
        raise_on_error (Optional[bool]): Whether or not to raise exceptions when they occur.
            Defaults to ``True``, since this is the most useful behavior in test.
        do_input_mapping (bool): Whether to map the op inputs to the outputs of the graph
            constructed around it.
        do_output_mapping (bool): Whether to map the op outputs to the outputs of the graph
            constructed around it.

    Returns:
        Union[CompositeSolidExecutionResult, SolidExecutionResult]: The result of executing the
        solid.
    """
    return (
        wrap_op_in_graph(
            op_def, tags, do_input_mapping=do_input_mapping, do_output_mapping=do_output_mapping
        )
        .to_job(logger_defs=logger_defs)
        .execute_in_process(
            resources=resources,
            input_values=input_values,
            raise_on_error=raise_on_error,
            run_config=run_config,
        )
    )


def execute_solid_within_pipeline(
    pipeline_def: PipelineDefinition,
    solid_name: str,
    inputs: Optional[Dict[str, object]] = None,
    run_config: Optional[Dict[str, object]] = None,
    mode: Optional[str] = None,
    preset: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    instance: Optional[DagsterInstance] = None,
) -> Union["CompositeSolidExecutionResult", "OpExecutionResult"]:
    """Execute a single solid within an existing pipeline.

    Intended to support tests. Input values may be passed directly.

    Args:
        pipeline_def (PipelineDefinition): The pipeline within which to execute the solid.
        solid_name (str): The name of the solid, or the aliased solid, to execute.
        inputs (Optional[Dict[str, Any]]): A dict of input names to input values, used to
            pass input values to the solid directly. You may also use the ``run_config`` to
            configure any inputs that are configurable.
        run_config (Optional[dict]): The configuration that parameterized this
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

    def __init__(self, artifacts_dir: str, inst_data: object = None):
        check.str_param(artifacts_dir, "artifacts_dir")
        self._artifacts_dir = artifacts_dir
        self._inst_data = inst_data

    @property
    def inst_data(self) -> object:
        return self._inst_data

    @classmethod
    def config_type(cls):
        return {"base_dir": str}

    @classmethod
    def from_config_value(
        cls, inst_data: object, config_value: Mapping[str, object]
    ) -> "FilesystemTestScheduler":
        artifacts_dir = cast(str, config_value["base_dir"])
        return FilesystemTestScheduler(artifacts_dir=artifacts_dir, inst_data=inst_data)

    def debug_info(self) -> str:
        return ""

    def get_logs_path(self, _instance: DagsterInstance, schedule_origin_id: str) -> str:
        check.str_param(schedule_origin_id, "schedule_origin_id")
        return os.path.join(self._artifacts_dir, "logs", schedule_origin_id, "scheduler.log")

    def wipe(self, instance: DagsterInstance) -> None:
        pass
