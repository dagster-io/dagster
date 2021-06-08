"""
This module contains the execution context objects that are internal to the system.
Not every property on these should be exposed to random Jane or Joe dagster user
so we have a different layer of objects that encode the explicit public API
in the user_context module
"""
from abc import ABC, abstractproperty
from typing import TYPE_CHECKING, Any, Dict, Iterable, NamedTuple, Optional, Set, cast

from dagster import check
from dagster.core.definitions.hook import HookDefinition
from dagster.core.definitions.mode import ModeDefinition
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.definitions.pipeline_base import IPipeline
from dagster.core.definitions.policy import RetryPolicy
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.definitions.resource import ScopedResourcesBuilder
from dagster.core.definitions.solid import SolidDefinition
from dagster.core.definitions.step_launcher import StepLauncher
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.execution.plan.step import ExecutionStep
from dagster.core.execution.retries import RetryMode
from dagster.core.executor.base import Executor
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.io_manager import IOManager
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.core.system_config.objects import ResolvedRunConfig
from dagster.core.types.dagster_type import DagsterType

from .input import InputContext
from .output import OutputContext, get_output_context

if TYPE_CHECKING:
    from dagster.core.definitions.intermediate_storage import IntermediateStorageDefinition
    from dagster.core.definitions.dependency import Solid, SolidHandle
    from dagster.core.storage.intermediate_storage import IntermediateStorage
    from dagster.core.instance import DagsterInstance
    from dagster.core.execution.plan.plan import ExecutionPlan
    from dagster.core.definitions.resource import Resources
    from .hook import HookContext


class IPlanContext(ABC):
    """Context interface to represent run information that does not require access to user code.

    The information available via this interface is accessible to the system throughout a run.
    """

    @abstractproperty
    def plan_data(self) -> "PlanData":
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
    resolved_run_config: ResolvedRunConfig
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

    def for_step(self, step: ExecutionStep, previous_attempt_count: int = 0) -> IStepContext:

        return StepExecutionContext(
            plan_data=self.plan_data,
            execution_data=self._execution_data,
            log_manager=self._log_manager.with_tags(**step.logging_tags),
            step=step,
            output_capture=self.output_capture,
            previous_attempt_count=previous_attempt_count,
        )

    @property
    def pipeline_def(self) -> PipelineDefinition:
        return self._execution_data.pipeline_def

    @property
    def resolved_run_config(self) -> ResolvedRunConfig:
        return self._execution_data.resolved_run_config

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
        return TypeCheckContext(
            self.run_id, self.log, self._execution_data.scoped_resources_builder, dagster_type
        )


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
        previous_attempt_count: int,
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
            execution_data.resolved_run_config,
            execution_data.intermediate_storage_def,
        )
        self._resources = execution_data.scoped_resources_builder.build(
            self._required_resource_keys
        )
        self._previous_attempt_count = previous_attempt_count

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

        self._step_exception = None
        self._step_output_capture: Dict[StepOutputHandle, Any] = {}

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

    @property
    def solid_retry_policy(self) -> Optional[RetryPolicy]:
        return self.pipeline_def.get_retry_policy_for_handle(self.solid_handle)

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

    def get_output_context(self, step_output_handle) -> OutputContext:
        return get_output_context(
            self.execution_plan,
            self.pipeline_def,
            self.resolved_run_config,
            step_output_handle,
            self._get_source_run_id(step_output_handle),
            log_manager=self.log,
            step_context=self,
            resources=None,
        )

    def for_input_manager(
        self,
        name: str,
        config: Any,
        metadata: Any,
        dagster_type: DagsterType,
        source_handle: Optional[StepOutputHandle] = None,
        resource_config: Any = None,
        resources: Optional["Resources"] = None,
    ) -> InputContext:
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
        from .hook import HookContext

        return HookContext(self, hook_def)

    def _get_source_run_id_from_logs(self, step_output_handle: StepOutputHandle) -> Optional[str]:
        from dagster.core.events import DagsterEventType

        # walk through event logs to find the right run_id based on the run lineage
        _, runs = self.instance.get_run_group(self.run_id)
        run_id_to_parent_run_id = {run.run_id: run.parent_run_id for run in runs}
        source_run_id = self.pipeline_run.parent_run_id
        while source_run_id:
            # note: this would cost N db calls where N = number of parent runs
            step_output_record = self.instance.all_logs(
                source_run_id, of_type=DagsterEventType.STEP_OUTPUT
            )
            # if the parent run has yielded an StepOutput event for the given step output,
            # we find the source run id
            if [
                r
                for r in step_output_record
                if r.dagster_event.step_key == step_output_handle.step_key
                and r.dagster_event.step_output_data.output_name == step_output_handle.output_name
            ]:
                return source_run_id
            else:
                # else, keep looking backwards
                source_run_id = run_id_to_parent_run_id.get(source_run_id)

        # when a fixed path is provided via io manager, it's able to run step subset using an execution
        # plan when the ascendant outputs were not previously created by dagster-controlled
        # computations. for example, in backfills, with fixed path io manager, we allow users to
        # "re-execute" runs with steps where the outputs weren't previously stored by dagster.
        return None

    def _get_source_run_id(self, step_output_handle: StepOutputHandle) -> Optional[str]:
        # determine if the step is not selected and
        if (
            # this is re-execution
            self.pipeline_run.parent_run_id
            # we are not re-executing the entire pipeline
            and self.pipeline_run.step_keys_to_execute is not None
            # this step is not being executed
            and step_output_handle.step_key not in self.pipeline_run.step_keys_to_execute
        ):
            return self._get_source_run_id_from_logs(step_output_handle)
        else:
            return self.pipeline_run.run_id

    def capture_step_exception(self, exception: BaseException):
        self._step_exception = check.inst_param(exception, "exception", BaseException)

    @property
    def step_exception(self) -> Optional[BaseException]:
        return self._step_exception

    @property
    def step_output_capture(self) -> Dict[StepOutputHandle, Any]:
        return self._step_output_capture

    @property
    def previous_attempt_count(self) -> int:
        return self._previous_attempt_count


class TypeCheckContext:
    """The ``context`` object available to a type check function on a DagsterType.

    Attributes:
        log (DagsterLogManager): Centralized log dispatch from user code.
        resources (Any): An object whose attributes contain the resources available to this solid.
        run_id (str): The id of this pipeline run.
    """

    def __init__(
        self,
        run_id: str,
        log_manager: DagsterLogManager,
        scoped_resources_builder: ScopedResourcesBuilder,
        dagster_type: DagsterType,
    ):
        self._run_id = run_id
        self._log = log_manager
        self._resources = scoped_resources_builder.build(dagster_type.required_resource_keys)

    @property
    def resources(self) -> "Resources":
        return self._resources

    @property
    def run_id(self) -> str:
        return self._run_id

    @property
    def log(self) -> DagsterLogManager:
        return self._log
