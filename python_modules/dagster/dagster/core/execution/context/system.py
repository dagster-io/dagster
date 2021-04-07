"""
This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module
"""
from abc import ABC, abstractmethod, abstractproperty
from collections import namedtuple
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, NamedTuple, Optional, Set, cast

from dagster import check
from dagster.core.definitions.hook import HookDefinition
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.pipeline_base import IPipeline
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.definitions.step_launcher import StepLauncher
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.step import ExecutionStep
from dagster.core.execution.plan.utils import build_resources_for_manager
from dagster.core.execution.retries import RetryMode
from dagster.core.executor.base import Executor
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.io_manager import IOManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.types.dagster_type import DagsterType, resolve_dagster_type

if TYPE_CHECKING:
    from dagster.core.definitions.intermediate_storage import IntermediateStorageDefinition
    from dagster.core.definitions.dependency import Solid, SolidHandle
    from dagster.core.storage.intermediate_storage import IntermediateStorage
    from dagster.core.instance import DagsterInstance
    from dagster.core.execution.plan.plan import ExecutionPlan
    from dagster.core.definitions.resource import Resources


class IPlanContext(ABC):
    """Context interface to represent run information that does not require access to user code.

    The information available via this interface is accessible to the system throughout a run.
    """

    @abstractproperty
    def plan_data(self) -> "PlanData":
        raise NotImplementedError()

    @abstractmethod
    def for_step(self, step: ExecutionStep) -> "IStepContext":
        raise NotImplementedError()

    @property
    def pipeline(self) -> IPipeline:
        return self.plan_data.pipeline

    @property
    def pipeline_run(self) -> PipelineRun:
        return self.plan_data.pipeline_run

    @property
    def run_id(self) -> str:
        return self.pipeline_run.run_id

    @property
    def run_config(self) -> dict:
        return self.pipeline_run.run_config

    @property
    def pipeline_name(self) -> str:
        return self.pipeline_run.pipeline_name

    @property
    def instance(self) -> "DagsterInstance":
        return self.plan_data.instance

    @property
    def raise_on_error(self) -> bool:
        return self.plan_data.raise_on_error

    @property
    def retry_mode(self) -> RetryMode:
        return self.plan_data.retry_mode

    @property
    def execution_plan(self):
        return self.plan_data.execution_plan

    @abstractproperty
    def output_capture(self) -> Optional[Dict[StepOutputHandle, Any]]:
        raise NotImplementedError()

    @property
    def log(self) -> DagsterLogManager:
        raise NotImplementedError()

    @property
    def logging_tags(self) -> Dict[str, str]:
        return self.log.logging_tags

    def has_tag(self, key: str) -> bool:
        check.str_param(key, "key")
        return key in self.logging_tags

    def get_tag(self, key: str) -> Optional[str]:
        check.str_param(key, "key")
        return self.logging_tags.get(key)


class PlanData(NamedTuple):
    """The data about a run that is available during both orchestration and execution.

    This object does not contain any information that requires access to user code, such as the
    pipeline definition, resources, or intermediate storage.
    """

    pipeline: IPipeline
    pipeline_run: PipelineRun
    instance: "DagsterInstance"
    execution_plan: "ExecutionPlan"
    raise_on_error: bool = False
    retry_mode: RetryMode = RetryMode.DISABLED


class ExecutionData(NamedTuple):
    """The data that is available to the system during execution.

    This object contains information that requires access to user code, such as the pipeline
    definition, resources, and intermediate storage.
    """

    scoped_resources_builder: ScopedResourcesBuilder
    intermediate_storage: "IntermediateStorage"
    intermediate_storage_def: "IntermediateStorageDefinition"
    environment_config: EnvironmentConfig
    pipeline_def: PipelineDefinition
    mode_def: ModeDefinition


class IStepContext(IPlanContext):
    """Interface to represent data to be available during either step orchestration or execution."""

    @abstractproperty
    def step(self) -> ExecutionStep:
        raise NotImplementedError()

    @abstractproperty
    def solid_handle(self) -> "SolidHandle":
        raise NotImplementedError()


class PlanOrchestrationContext(IPlanContext):
    """Context for the orchestration of a run.

    This context assumes inability to run user code directly.
    """

    def __init__(
        self,
        plan_data: PlanData,
        log_manager: DagsterLogManager,
        executor: Executor,
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        self._plan_data = plan_data
        self._log_manager = log_manager
        self._executor = executor
        self._output_capture = output_capture

    @property
    def plan_data(self) -> PlanData:
        return self._plan_data

    @property
    def reconstructable_pipeline(self) -> ReconstructablePipeline:
        if not isinstance(self.pipeline, ReconstructablePipeline):
            raise DagsterInvariantViolationError(
                "reconstructable_pipeline property must be a ReconstructablePipeline"
            )
        return self.pipeline

    @property
    def log(self) -> DagsterLogManager:
        return self._log_manager

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def output_capture(self) -> Optional[Dict[StepOutputHandle, Any]]:
        return self._output_capture

    def for_step(self, step: ExecutionStep) -> "IStepContext":
        return StepOrchestrationContext(
            plan_data=self.plan_data,
            log_manager=self._log_manager.with_tags(**step.logging_tags),
            executor=self.executor,
            step=step,
            output_capture=self.output_capture,
        )


class StepOrchestrationContext(PlanOrchestrationContext, IStepContext):
    """Context for the orchestration of a step.

    This context assumes inability to run user code directly. Thus, it does not include any resource
    or intermediate storage information.
    """

    def __init__(self, plan_data, log_manager, executor, step, output_capture):
        super(StepOrchestrationContext, self).__init__(
            plan_data, log_manager, executor, output_capture
        )
        self._step = step

    @property
    def step(self) -> ExecutionStep:
        return self._step

    @property
    def solid_handle(self) -> "SolidHandle":
        return self.step.solid_handle


class PlanExecutionContext(IPlanContext):
    """Context for the execution of a plan.

    This context assumes that user code can be run directly, and thus includes resource and
    intermediate storage information.
    """

    def __init__(
        self,
        plan_data: PlanData,
        execution_data: ExecutionData,
        log_manager: DagsterLogManager,
        output_capture: Optional[Dict[StepOutputHandle, Any]] = None,
    ):
        self._plan_data = plan_data
        self._execution_data = execution_data
        self._log_manager = log_manager
        self._output_capture = output_capture

    @property
    def plan_data(self) -> PlanData:
        return self._plan_data

    @property
    def output_capture(self) -> Optional[Dict[StepOutputHandle, Any]]:
        return self._output_capture

    def for_step(self, step: ExecutionStep) -> IStepContext:
        return StepExecutionContext(
            plan_data=self.plan_data,
            execution_data=self._execution_data,
            log_manager=self._log_manager.with_tags(**step.logging_tags),
            step=step,
            output_capture=self.output_capture,
        )

    @property
    def pipeline_def(self) -> PipelineDefinition:
        return self._execution_data.pipeline_def

    @property
    def environment_config(self) -> EnvironmentConfig:
        return self._execution_data.environment_config

    @property
    def intermediate_storage_def(self) -> "IntermediateStorageDefinition":
        return self._execution_data.intermediate_storage_def

    @property
    def intermediate_storage(self) -> "IntermediateStorage":
        return self._execution_data.intermediate_storage

    @property
    def scoped_resources_builder(self) -> ScopedResourcesBuilder:
        return self._execution_data.scoped_resources_builder

    @property
    def log(self) -> DagsterLogManager:
        return self._log_manager

    def for_type(self, dagster_type: DagsterType) -> "TypeCheckContext":
        return TypeCheckContext(self, dagster_type)


class StepExecutionContext(PlanExecutionContext, IStepContext):
    """Context for the execution of a step.

    This context assumes that user code can be run directly, and thus includes resource and
    intermediate storage information.
    """

    def __init__(
        self,
        plan_data: PlanData,
        execution_data: ExecutionData,
        log_manager: DagsterLogManager,
        step: ExecutionStep,
        output_capture: Optional[Dict[StepOutputHandle, Any]],
    ):
        from dagster.core.execution.resources_init import get_required_resource_keys_for_step

        super(StepExecutionContext, self).__init__(
            plan_data=plan_data,
            execution_data=execution_data,
            log_manager=log_manager,
            output_capture=output_capture,
        )
        self._step = step
        self._required_resource_keys = get_required_resource_keys_for_step(
            plan_data.pipeline.get_definition(),
            step,
            plan_data.execution_plan,
            execution_data.environment_config,
            execution_data.intermediate_storage_def,
        )
        self._resources = execution_data.scoped_resources_builder.build(
            self._required_resource_keys
        )

        resources_iter = cast(Iterable, self._resources)

        step_launcher_resources = [
            resource for resource in resources_iter if isinstance(resource, StepLauncher)
        ]

        self._step_launcher: Optional[StepLauncher] = None
        if len(step_launcher_resources) > 1:
            raise DagsterInvariantViolationError(
                "Multiple required resources for solid {solid_name} have inherit StepLauncher"
                "There should be at most one step launcher resource per solid.".format(
                    solid_name=step.solid_handle.name
                )
            )
        elif len(step_launcher_resources) == 1:
            self._step_launcher = step_launcher_resources[0]

    @property
    def step(self) -> ExecutionStep:
        return self._step

    @property
    def solid_handle(self) -> "SolidHandle":
        return self.step.solid_handle

    @property
    def required_resource_keys(self) -> Set[str]:
        return self._required_resource_keys

    @property
    def resources(self) -> "Resources":
        return self._resources

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        return self._step_launcher

    @property
    def solid_def(self) -> SolidDefinition:
        return self.solid.definition

    @property
    def pipeline_def(self) -> PipelineDefinition:
        return self._execution_data.pipeline_def

    @property
    def mode_def(self) -> ModeDefinition:
        return self._execution_data.mode_def

    @property
    def solid(self) -> "Solid":
        return self.pipeline_def.get_solid(self._step.solid_handle)

    def get_io_manager(self, step_output_handle) -> IOManager:
        step_output = self.execution_plan.get_step_output(step_output_handle)
        io_manager_key = (
            self.pipeline_def.get_solid(step_output.solid_handle)
            .output_def_named(step_output.name)
            .io_manager_key
        )

        # backcompat: if intermediate storage is specified and the user hasn't overridden
        # io_manager_key on the output, use the intermediate storage.
        if io_manager_key == "io_manager" and not self.using_default_intermediate_storage():
            from dagster.core.storage.intermediate_storage import IntermediateStorageAdapter

            output_manager = IntermediateStorageAdapter(self.intermediate_storage)
        else:
            output_manager = getattr(self.resources, io_manager_key)
        return check.inst(output_manager, IOManager)

    def using_default_intermediate_storage(self) -> bool:
        from dagster.core.storage.system_storage import mem_intermediate_storage

        # pylint: disable=comparison-with-callable
        return (
            self.intermediate_storage_def is None
            or self.intermediate_storage_def == mem_intermediate_storage
        )

    def get_output_context(self, step_output_handle) -> "OutputContext":
        return get_output_context(
            self.execution_plan,
            self.pipeline_def,
            self.environment_config,
            step_output_handle,
            self._get_source_run_id(step_output_handle),
            log_manager=self.log,
            step_context=self,
        )

    def for_input_manager(
        self,
        name: str,
        config: dict,
        metadata: Any,
        dagster_type: DagsterType,
        source_handle: Optional[StepOutputHandle] = None,
        resource_config: Any = None,
        resources: Optional["Resources"] = None,
    ) -> "InputContext":
        return InputContext(
            pipeline_name=self.pipeline_def.name,
            name=name,
            solid_def=self.solid_def,
            config=config,
            metadata=metadata,
            upstream_output=self.get_output_context(source_handle) if source_handle else None,
            dagster_type=dagster_type,
            log_manager=self.log,
            step_context=self,
            resource_config=resource_config,
            resources=resources,
        )

    def for_hook(self, hook_def: HookDefinition) -> "HookContext":
        return HookContext(self, hook_def)

    def _get_source_run_id(self, step_output_handle: StepOutputHandle) -> str:
        # determine if the step is skipped
        if (
            # this is re-execution
            self.pipeline_run.parent_run_id
            # we are not re-executing the entire pipeline
            and self.pipeline_run.step_keys_to_execute is not None
            # this step is not being executed
            and step_output_handle.step_key not in self.pipeline_run.step_keys_to_execute
        ):
            return self.pipeline_run.parent_run_id
        else:
            return self.pipeline_run.run_id


class TypeCheckContext:
    """The ``context`` object available to a type check function on a DagsterType.

    Attributes:
        log (DagsterLogManager): Centralized log dispatch from user code.
        resources (Any): An object whose attributes contain the resources available to this solid.
        run_id (str): The id of this pipeline run.
    """

    def __init__(
        self,
        plan_execution_context: PlanExecutionContext,
        dagster_type: DagsterType,
    ):
        self._plan_execution_context = plan_execution_context
        self._resources = plan_execution_context.scoped_resources_builder.build(
            dagster_type.required_resource_keys
        )

    @property
    def resources(self) -> "Resources":
        return self._resources

    @property
    def run_id(self) -> str:
        return self._plan_execution_context.run_id

    @property
    def log(self) -> DagsterLogManager:
        return self._plan_execution_context.log


# HookContext currently uses undocumented attributes that are pulled from the step context for event
# recording and logging. These should be removed, and the callsites should be changed to use the
# step context instead.
class HookContext:
    """The ``context`` object available to a hook function on an DagsterEvent.

    Attributes:
        log (DagsterLogManager): Centralized log dispatch from user code.
        hook_def (HookDefinition): The hook that the context object belongs to.
        solid (Solid): The solid instance associated with the hook.
        resources (NamedTuple): Resources available in the hook context.
        solid_config (Any): The parsed config specific to this solid.
    """

    def __init__(
        self,
        step_execution_context: StepExecutionContext,
        hook_def: HookDefinition,
    ):
        self._step_execution_context = step_execution_context
        self._hook_def = check.inst_param(hook_def, "hook_def", HookDefinition)
        self._required_resource_keys = hook_def.required_resource_keys
        self._resources = step_execution_context.scoped_resources_builder.build(
            self._required_resource_keys
        )

    @property
    def hook_def(self) -> HookDefinition:
        return self._hook_def

    @property
    def run_id(self) -> str:
        return self._step_execution_context.run_id

    @property
    def solid(self) -> "Solid":
        return self._step_execution_context.solid

    @property
    def resources(self) -> "Resources":
        return self._resources

    @property
    def required_resource_keys(self) -> Set[str]:
        return self._required_resource_keys

    @property
    def solid_config(self) -> Any:
        solid_config = self._step_execution_context.environment_config.solids.get(
            str(self._step_execution_context.step.solid_handle)
        )
        return solid_config.config if solid_config else None

    @property
    def log(self) -> DagsterLogManager:
        return self._step_execution_context.log

    @property
    def pipeline_name(self) -> str:
        return self._step_execution_context.pipeline_name

    @property
    def step(self) -> ExecutionStep:
        return self._step_execution_context.step

    @property
    def logging_tags(self) -> Dict[str, str]:
        return self._step_execution_context.logging_tags


class OutputContext(
    namedtuple(
        "_OutputContext",
        "step_key name pipeline_name run_id metadata mapping_key config solid_def dagster_type log version step_context resource_config resources",
    )
):
    """
    The context object that is available to the `handle_output` method of an :py:class:`IOManager`.

    Attributes:
        step_key (str): The step_key for the compute step that produced the output.
        name (str): The name of the output that produced the output.
        pipeline_name (str): The name of the pipeline definition.
        run_id (Optional[str]): The id of the run that produced the output.
        metadata (Optional[Dict[str, Any]]): A dict of the metadata that is assigned to the
            OutputDefinition that produced the output.
        mapping_key (Optional[str]): The key that identifies a unique mapped output. None for regular outputs.
        config (Optional[Any]): The configuration for the output.
        solid_def (Optional[SolidDefinition]): The definition of the solid that produced the output.
        dagster_type (Optional[DagsterType]): The type of this output.
        log (Optional[DagsterLogManager]): The log manager to use for this output.
        version (Optional[str]): (Experimental) The version of the output.
        resources (Optional[ScopedResources]): The resources required by the output manager, specified by the
            `required_resource_keys` parameter.
    """

    def __new__(
        cls,
        step_key: str,
        name: str,
        pipeline_name: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mapping_key: Optional[str] = None,
        config: Any = None,
        solid_def: Optional[SolidDefinition] = None,
        dagster_type: Optional[DagsterType] = None,
        log_manager: Optional[DagsterLogManager] = None,
        version: Optional[str] = None,
        # This is used internally by the intermediate storage adapter, we don't usually expect users to mock this.
        step_context: Optional[StepExecutionContext] = None,
        resource_config: Optional[Any] = None,
        resources: Optional["Resources"] = None,
    ):

        return super(OutputContext, cls).__new__(
            cls,
            step_key=check.str_param(step_key, "step_key"),
            name=check.str_param(name, "name"),
            pipeline_name=check.opt_str_param(pipeline_name, "pipeline_name"),
            run_id=check.opt_str_param(run_id, "run_id"),
            metadata=check.opt_dict_param(metadata, "metadata"),
            mapping_key=check.opt_str_param(mapping_key, "mapping_key"),
            config=config,
            solid_def=check.opt_inst_param(solid_def, "solid_def", SolidDefinition),
            dagster_type=check.inst_param(
                resolve_dagster_type(dagster_type), "dagster_type", DagsterType
            ),  # this allows the user to mock the context with unresolved dagster type
            log=check.opt_inst_param(log_manager, "log_manager", DagsterLogManager),
            version=check.opt_str_param(version, "version"),
            step_context=check.opt_inst_param(step_context, "step_context", StepExecutionContext),
            resource_config=resource_config,
            resources=resources,
        )

    def get_run_scoped_output_identifier(self) -> List[str]:
        """Utility method to get a collection of identifiers that as a whole represent a unique
        step output.

        The unique identifier collection consists of

        - ``run_id``: the id of the run which generates the output.
            Note: This method also handles the re-execution memoization logic. If the step that
            generates the output is skipped in the re-execution, the ``run_id`` will be the id
            of its parent run.
        - ``step_key``: the key for a compute step.
        - ``name``: the name of the output. (default: 'result').

        Returns:
            List[str, ...]: A list of identifiers, i.e. run id, step key, and output name
        """
        if self.mapping_key:
            return [self.run_id, self.step_key, self.name, self.mapping_key]

        return [self.run_id, self.step_key, self.name]


class InputContext(
    namedtuple(
        "_InputContext",
        "name pipeline_name solid_def config metadata upstream_output dagster_type log step_context resource_config resources",
    )
):
    """
    The ``context`` object available to the load_input method of :py:class:`RootInputManager`.

    Attributes:
        name (Optional[str]): The name of the input that we're loading.
        pipeline_name (Optional[str]): The name of the pipeline.
        solid_def (Optional[SolidDefinition]): The definition of the solid that's loading the input.
        config (Optional[Any]): The config attached to the input that we're loading.
        metadata (Optional[Dict[str, Any]]): A dict of metadata that is assigned to the
            InputDefinition that we're loading for.
        upstream_output (Optional[OutputContext]): Info about the output that produced the object
            we're loading.
        dagster_type (Optional[DagsterType]): The type of this input.
        log (Optional[DagsterLogManager]): The log manager to use for this input.
        resource_config (Optional[Dict[str, Any]]): The config associated with the resource that
            initializes the RootInputManager.
        resources (ScopedResources): The resources required by the resource that initializes the
            input manager. If using the :py:func:`@root_input_manager` decorator, these resources
            correspond to those requested with the `required_resource_keys` parameter.
    """

    def __new__(
        cls,
        pipeline_name: Optional[str] = None,
        # This will be None when called from calling SolidExecutionResult.output_value
        name: Optional[str] = None,
        solid_def: Optional[SolidDefinition] = None,
        config: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        upstream_output: Optional[OutputContext] = None,
        dagster_type: Optional[DagsterType] = None,
        log_manager: Optional[DagsterLogManager] = None,
        # This is used internally by the intermediate storage adapter, we don't expect users to mock this.
        step_context: Optional[StepExecutionContext] = None,
        resource_config: Any = None,
        resources: Optional["Resources"] = None,
    ):

        return super(InputContext, cls).__new__(
            cls,
            name=check.opt_str_param(name, "name"),
            pipeline_name=check.opt_str_param(pipeline_name, "pipeline_name"),
            solid_def=check.opt_inst_param(solid_def, "solid_def", SolidDefinition),
            config=config,
            metadata=metadata,
            upstream_output=check.opt_inst_param(upstream_output, "upstream_output", OutputContext),
            dagster_type=check.inst_param(
                resolve_dagster_type(dagster_type), "dagster_type", DagsterType
            ),  # this allows the user to mock the context with unresolved dagster type
            log=check.opt_inst_param(log_manager, "log_manager", DagsterLogManager),
            step_context=check.opt_inst_param(step_context, "step_context", StepExecutionContext),
            resource_config=resource_config,
            resources=resources,
        )


def _step_output_version(
    pipeline_def: PipelineDefinition,
    execution_plan: "ExecutionPlan",
    environment_config: "EnvironmentConfig",
    step_output_handle: StepOutputHandle,
) -> Optional[str]:
    from dagster.core.execution.resolve_versions import resolve_step_output_versions

    step_output_versions = resolve_step_output_versions(
        pipeline_def, execution_plan, environment_config
    )
    return (
        step_output_versions[step_output_handle]
        if step_output_handle in step_output_versions
        else None
    )


def get_output_context(
    execution_plan: "ExecutionPlan",
    pipeline_def: PipelineDefinition,
    environment_config: EnvironmentConfig,
    step_output_handle: StepOutputHandle,
    run_id: Optional[str] = None,
    log_manager: Optional[DagsterLogManager] = None,
    step_context: Optional[StepExecutionContext] = None,
) -> OutputContext:
    """
    Args:
        run_id (str): The run ID of the run that produced the output, not necessarily the run that
            the context will be used in.
    """
    from dagster.core.execution.plan.plan import ExecutionPlan

    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(environment_config, "environment_config", EnvironmentConfig)
    check.inst_param(step_output_handle, "step_output_handle", StepOutputHandle)
    check.opt_str_param(run_id, "run_id")

    step = execution_plan.get_step_by_key(step_output_handle.step_key)
    # get config
    solid_config = environment_config.solids.get(step.solid_handle.to_string())
    outputs_config = solid_config.outputs

    if outputs_config:
        output_config = outputs_config.get_output_manager_config(step_output_handle.output_name)
    else:
        output_config = None

    step_output = execution_plan.get_step_output(step_output_handle)
    output_def = pipeline_def.get_solid(step_output.solid_handle).output_def_named(step_output.name)

    io_manager_key = output_def.io_manager_key
    resource_config = environment_config.resources[io_manager_key].config

    resources = build_resources_for_manager(io_manager_key, step_context) if step_context else None

    return OutputContext(
        step_key=step_output_handle.step_key,
        name=step_output_handle.output_name,
        pipeline_name=pipeline_def.name,
        run_id=run_id,
        metadata=output_def.metadata,
        mapping_key=step_output_handle.mapping_key,
        config=output_config,
        solid_def=pipeline_def.get_solid(step.solid_handle).definition,
        dagster_type=output_def.dagster_type,
        log_manager=log_manager,
        version=(
            _step_output_version(
                pipeline_def, execution_plan, environment_config, step_output_handle
            )
            if MEMOIZED_RUN_TAG in pipeline_def.tags
            else None
        ),
        step_context=step_context,
        resource_config=resource_config,
        resources=resources,
    )
