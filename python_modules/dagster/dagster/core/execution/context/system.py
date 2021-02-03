"""
This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module
"""
from collections import namedtuple
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional, Set

from dagster import check
from dagster.core.definitions.hook import HookDefinition
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.pipeline_base import IPipeline
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.definitions.step_launcher import StepLauncher
from dagster.core.errors import DagsterInvalidPropertyError, DagsterInvariantViolationError
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.step import ExecutionStep
from dagster.core.execution.plan.utils import build_resources_for_manager
from dagster.core.execution.retries import Retries
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


class SystemExecutionContextData(
    namedtuple(
        "_SystemExecutionContextData",
        (
            "pipeline_run scoped_resources_builder environment_config pipeline "
            "mode_def intermediate_storage_def instance intermediate_storage "
            "raise_on_error retries execution_plan"
        ),
    )
):
    """
    SystemExecutionContextData is the data that remains constant throughout the entire
    execution of a pipeline or plan.
    """

    def __new__(
        cls,
        pipeline_run: PipelineRun,
        scoped_resources_builder: ScopedResourcesBuilder,
        environment_config: EnvironmentConfig,
        pipeline: IPipeline,
        mode_def: ModeDefinition,
        intermediate_storage_def: Optional["IntermediateStorageDefinition"],
        instance: "DagsterInstance",
        intermediate_storage: "IntermediateStorage",
        raise_on_error: bool,
        retries: Retries,
        execution_plan: "ExecutionPlan",
    ):
        from dagster.core.definitions.intermediate_storage import IntermediateStorageDefinition
        from dagster.core.storage.intermediate_storage import IntermediateStorage
        from dagster.core.instance import DagsterInstance
        from dagster.core.execution.plan.plan import ExecutionPlan

        return super(SystemExecutionContextData, cls).__new__(
            cls,
            pipeline_run=check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            scoped_resources_builder=check.inst_param(
                scoped_resources_builder, "scoped_resources_builder", ScopedResourcesBuilder
            ),
            environment_config=check.inst_param(
                environment_config, "environment_config", EnvironmentConfig
            ),
            pipeline=check.inst_param(pipeline, "pipeline", IPipeline),
            mode_def=check.inst_param(mode_def, "mode_def", ModeDefinition),
            intermediate_storage_def=check.opt_inst_param(
                intermediate_storage_def, "intermediate_storage_def", IntermediateStorageDefinition
            ),
            instance=check.inst_param(instance, "instance", DagsterInstance),
            intermediate_storage=check.inst_param(
                intermediate_storage, "intermediate_storage", IntermediateStorage
            ),
            raise_on_error=check.bool_param(raise_on_error, "raise_on_error"),
            retries=check.inst_param(retries, "retries", Retries),
            execution_plan=check.inst_param(execution_plan, "execution_plan", ExecutionPlan),
        )

    @property
    def run_id(self) -> str:
        return self.pipeline_run.run_id

    @property
    def run_config(self) -> dict:
        return self.environment_config.original_config_dict

    @property
    def pipeline_name(self) -> str:
        return self.pipeline_run.pipeline_name


class SystemExecutionContext:
    __slots__ = ["_execution_context_data", "_log_manager"]

    def __init__(
        self, execution_context_data: SystemExecutionContextData, log_manager: DagsterLogManager
    ):
        self._execution_context_data = check.inst_param(
            execution_context_data, "execution_context_data", SystemExecutionContextData
        )
        self._log_manager = check.inst_param(log_manager, "log_manager", DagsterLogManager)

    @property
    def pipeline_run(self) -> PipelineRun:
        return self._execution_context_data.pipeline_run

    @property
    def scoped_resources_builder(self) -> ScopedResourcesBuilder:
        return self._execution_context_data.scoped_resources_builder

    @property
    def run_id(self) -> str:
        return self._execution_context_data.run_id

    @property
    def run_config(self) -> dict:
        return self._execution_context_data.run_config

    @property
    def environment_config(self) -> EnvironmentConfig:
        return self._execution_context_data.environment_config

    @property
    def pipeline(self) -> IPipeline:
        return self._execution_context_data.pipeline

    @property
    def pipeline_name(self) -> str:
        return self._execution_context_data.pipeline_name

    @property
    def mode_def(self) -> ModeDefinition:
        return self._execution_context_data.mode_def

    @property
    def intermediate_storage_def(self) -> "IntermediateStorageDefinition":
        return self._execution_context_data.intermediate_storage_def

    @property
    def instance(self) -> "DagsterInstance":
        return self._execution_context_data.instance

    @property
    def intermediate_storage(self):
        return self._execution_context_data.intermediate_storage

    @property
    def file_manager(self) -> None:
        raise DagsterInvalidPropertyError(
            "You have attempted to access the file manager which has been moved to resources in 0.10.0. "
            "Please access it via `context.resources.file_manager` instead."
        )

    @property
    def raise_on_error(self) -> bool:
        return self._execution_context_data.raise_on_error

    @property
    def retries(self) -> Retries:
        return self._execution_context_data.retries

    @property
    def log(self) -> DagsterLogManager:
        return self._log_manager

    @property
    def logging_tags(self) -> Dict[str, str]:
        return self._log_manager.logging_tags

    @property
    def execution_plan(self):
        return self._execution_context_data.execution_plan

    def has_tag(self, key: str) -> bool:
        check.str_param(key, "key")
        return key in self.logging_tags

    def get_tag(self, key: str) -> Optional[str]:
        check.str_param(key, "key")
        return self.logging_tags.get(key)

    def for_step(self, step: ExecutionStep) -> "SystemStepExecutionContext":

        check.inst_param(step, "step", ExecutionStep)

        return SystemStepExecutionContext(
            self._execution_context_data, self._log_manager.with_tags(**step.logging_tags), step,
        )

    def for_type(self, dagster_type: DagsterType) -> "TypeCheckContext":
        return TypeCheckContext(self._execution_context_data, self.log, dagster_type)


class SystemPipelineExecutionContext(SystemExecutionContext):
    __slots__ = ["_executor"]

    def __init__(
        self,
        execution_context_data: SystemExecutionContextData,
        log_manager: DagsterLogManager,
        executor: Executor,
    ):
        super(SystemPipelineExecutionContext, self).__init__(execution_context_data, log_manager)
        self._executor = check.inst_param(executor, "executor", Executor)

    @property
    def executor(self) -> Executor:
        return self._executor


class SystemStepExecutionContext(SystemExecutionContext):
    __slots__ = ["_step", "_resources", "_required_resource_keys", "_step_launcher"]

    def __init__(
        self,
        execution_context_data: SystemExecutionContextData,
        log_manager: DagsterLogManager,
        step: ExecutionStep,
    ):
        from dagster.core.execution.resources_init import get_required_resource_keys_for_step

        self._step = check.inst_param(step, "step", ExecutionStep)
        super(SystemStepExecutionContext, self).__init__(execution_context_data, log_manager)
        self._required_resource_keys = get_required_resource_keys_for_step(
            step,
            execution_context_data.execution_plan,
            execution_context_data.intermediate_storage_def,
        )
        self._resources = self._execution_context_data.scoped_resources_builder.build(
            self._required_resource_keys
        )
        step_launcher_resources = [
            resource for resource in self._resources if isinstance(resource, StepLauncher)
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

        self._log_manager = log_manager

    def for_compute(self) -> "SystemComputeExecutionContext":
        return SystemComputeExecutionContext(self._execution_context_data, self.log, self.step)

    @property
    def step(self) -> ExecutionStep:
        return self._step

    @property
    def step_launcher(self) -> Optional[StepLauncher]:
        return self._step_launcher

    @property
    def solid_handle(self) -> "SolidHandle":
        return self._step.solid_handle

    @property
    def solid_def(self) -> SolidDefinition:
        return self.solid.definition

    @property
    def pipeline_def(self) -> PipelineDefinition:
        return self._execution_context_data.pipeline.get_definition()

    @property
    def solid(self) -> "Solid":
        return self.pipeline_def.get_solid(self._step.solid_handle)

    @property
    def resources(self) -> NamedTuple:
        return self._resources

    @property
    def required_resource_keys(self) -> Set[str]:
        return self._required_resource_keys

    @property
    def log(self) -> DagsterLogManager:
        return self._log_manager

    def for_hook(self, hook_def: HookDefinition) -> "HookContext":
        return HookContext(self._execution_context_data, self.log, hook_def, self.step)

    def _get_source_run_id(self, step_output_handle: StepOutputHandle) -> str:
        # determine if the step is skipped
        if (
            # this is re-execution
            self.pipeline_run.parent_run_id
            # only part of the pipeline is being re-executed
            and len(self.execution_plan.step_handles_to_execute) < len(self.execution_plan.steps)
            # this step is not being executed
            and step_output_handle.step_key not in self.execution_plan.step_handles_to_execute
        ):
            return self.pipeline_run.parent_run_id
        else:
            return self.pipeline_run.run_id

    def get_output_context(self, step_output_handle) -> "OutputContext":
        return get_output_context(
            self.execution_plan,
            self.environment_config,
            step_output_handle,
            self._get_source_run_id(step_output_handle),
            log_manager=self._log_manager,
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
        resources: Optional[NamedTuple] = None,
    ) -> "InputContext":
        return InputContext(
            pipeline_name=self.pipeline_def.name,
            name=name,
            solid_def=self.solid_def,
            config=config,
            metadata=metadata,
            upstream_output=self.get_output_context(source_handle) if source_handle else None,
            dagster_type=dagster_type,
            log_manager=self._log_manager,
            step_context=self,
            resource_config=resource_config,
            resources=resources,
        )

    def using_default_intermediate_storage(self) -> bool:
        from dagster.core.storage.system_storage import mem_intermediate_storage

        # pylint: disable=comparison-with-callable
        return (
            self.intermediate_storage_def is None
            or self.intermediate_storage_def == mem_intermediate_storage
        )

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


class SystemComputeExecutionContext(SystemStepExecutionContext):
    @property
    def solid_config(self) -> Any:
        solid_config = self.environment_config.solids.get(str(self.solid_handle))
        return solid_config.config if solid_config else None


class TypeCheckContext(SystemExecutionContext):
    """The ``context`` object available to a type check function on a DagsterType.

    Attributes:
        log (DagsterLogManager): Centralized log dispatch from user code.
        resources (Any): An object whose attributes contain the resources available to this solid.
        run_id (str): The id of this pipeline run.
    """

    def __init__(
        self,
        execution_context_data: SystemExecutionContextData,
        log_manager: DagsterLogManager,
        dagster_type: DagsterType,
    ):
        super(TypeCheckContext, self).__init__(execution_context_data, log_manager)
        self._resources = self._execution_context_data.scoped_resources_builder.build(
            dagster_type.required_resource_keys
        )
        self._log_manager = log_manager

    @property
    def resources(self) -> NamedTuple:
        return self._resources


class HookContext(SystemExecutionContext):
    """The ``context`` object available to a hook function on an DagsterEvent.

    Attributes:
        log (DagsterLogManager): Centralized log dispatch from user code.
        hook_def (HookDefinition): The hook that the context object belongs to.
        step (ExecutionStep): The compute step associated with the hook.
        solid (Solid): The solid instance associated with the hook.
        resources (NamedTuple): Resources available in the hook context.
        solid_config (Any): The parsed config specific to this solid.
    """

    def __init__(
        self,
        execution_context_data: SystemExecutionContextData,
        log_manager: DagsterLogManager,
        hook_def: HookDefinition,
        step: ExecutionStep,
    ):

        super(HookContext, self).__init__(execution_context_data, log_manager)
        self._log_manager = log_manager
        self._hook_def = check.inst_param(hook_def, "hook_def", HookDefinition)
        self._step = check.inst_param(step, "step", ExecutionStep)

        self._required_resource_keys = hook_def.required_resource_keys
        self._resources = self._execution_context_data.scoped_resources_builder.build(
            self._required_resource_keys
        )

    @property
    def hook_def(self) -> HookDefinition:
        return self._hook_def

    @property
    def step(self) -> ExecutionStep:
        return self._step

    @property
    def pipeline_def(self) -> PipelineDefinition:
        return self._execution_context_data.pipeline.get_definition()

    @property
    def solid(self) -> "Solid":
        return self.pipeline_def.get_solid(self._step.solid_handle)

    @property
    def resources(self) -> NamedTuple:
        return self._resources

    @property
    def required_resource_keys(self) -> Set[str]:
        return self._required_resource_keys

    @property
    def solid_config(self) -> Any:
        solid_config = self.environment_config.solids.get(str(self._step.solid_handle))
        return solid_config.config if solid_config else None


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
        pipeline_name: str,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        mapping_key: Optional[str] = None,
        config: Any = None,
        solid_def: Optional[SolidDefinition] = None,
        dagster_type: Optional[DagsterType] = None,
        log_manager: Optional[DagsterLogManager] = None,
        version: Optional[str] = None,
        # This is used internally by the intermediate storage adapter, we don't usually expect users to mock this.
        step_context: Optional[SystemStepExecutionContext] = None,
        resource_config: Optional[Any] = None,
        resources: Optional[NamedTuple] = None,
    ):

        return super(OutputContext, cls).__new__(
            cls,
            step_key=check.str_param(step_key, "step_key"),
            name=check.str_param(name, "name"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
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
            step_context=check.opt_inst_param(
                step_context, "step_context", SystemStepExecutionContext
            ),
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
        pipeline_name (str): The name of the pipeline.
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
        pipeline_name: str,
        # This will be None when called from calling SolidExecutionResult.output_value
        name: Optional[str] = None,
        solid_def: Optional[SolidDefinition] = None,
        config: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
        upstream_output: Optional[OutputContext] = None,
        dagster_type: Optional[DagsterType] = None,
        log_manager: Optional[DagsterLogManager] = None,
        # This is used internally by the intermediate storage adapter, we don't expect users to mock this.
        step_context: Optional[SystemStepExecutionContext] = None,
        resource_config: Any = None,
        resources: Optional[NamedTuple] = None,
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
            step_context=check.opt_inst_param(
                step_context, "step_context", SystemStepExecutionContext
            ),
            resource_config=resource_config,
            resources=resources,
        )


def _step_output_version(
    execution_plan: "ExecutionPlan", step_output_handle: StepOutputHandle
) -> Optional[str]:
    step_output_versions = execution_plan.resolve_step_output_versions()
    return (
        step_output_versions[step_output_handle]
        if step_output_handle in step_output_versions
        else None
    )


def get_output_context(
    execution_plan: "ExecutionPlan",
    environment_config: EnvironmentConfig,
    step_output_handle: StepOutputHandle,
    run_id: str,
    log_manager: Optional[DagsterLogManager] = None,
    step_context: Optional[SystemStepExecutionContext] = None,
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

    pipeline_def = execution_plan.pipeline.get_definition()

    step_output = execution_plan.get_step_output(step_output_handle)
    output_def = pipeline_def.get_solid(step_output.solid_handle).output_def_named(step_output.name)

    io_manager_key = output_def.io_manager_key
    resource_config = environment_config.resources[io_manager_key].get("config", {})

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
        version=_step_output_version(execution_plan, step_output_handle)
        if MEMOIZED_RUN_TAG in execution_plan.pipeline.get_definition().tags
        else None,
        step_context=step_context,
        resource_config=resource_config,
        resources=resources,
    )
