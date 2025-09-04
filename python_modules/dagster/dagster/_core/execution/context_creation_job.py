import asyncio
import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import Generator, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Generic,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    cast,
)

from dagster_shared.error import DagsterError

import dagster._check as check
from dagster._core.definitions import ExecutorDefinition, JobDefinition
from dagster._core.definitions.executor_definition import check_cross_process_constraints
from dagster._core.definitions.job_base import IJob
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.definitions.resource_definition import ScopedResourcesBuilder
from dagster._core.events import DagsterEvent, RunFailureReason
from dagster._core.execution.context.logger import InitLoggerContext
from dagster._core.execution.context.system import (
    ExecutionData,
    IPlanContext,
    PlanData,
    PlanExecutionContext,
    PlanOrchestrationContext,
)
from dagster._core.execution.memoization import validate_reexecution_memoization
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.resources_init import (
    get_required_resource_keys_to_init,
    resource_initialization_manager,
)
from dagster._core.execution.retries import RetryMode
from dagster._core.execution.step_dependency_config import StepDependencyConfig
from dagster._core.executor.init import InitExecutorContext
from dagster._core.instance import DagsterInstance
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._loggers import default_loggers, default_system_loggers
from dagster._utils import EventGenerationManager
from dagster._utils.error import serializable_error_info_from_exc_info

if TYPE_CHECKING:
    from dagster._core.errors import DagsterUserCodeExecutionError
    from dagster._core.execution.plan.outputs import StepOutputHandle
    from dagster._core.executor.base import Executor

    # Import within functions so that we can mock the class in tests using freeze_time.
    # Essentially, we want to be able to control the timestamp of the log records.
    from dagster._core.log_manager import DagsterLogManager


def initialize_console_manager(
    dagster_run: Optional[DagsterRun], instance: Optional[DagsterInstance] = None
) -> "DagsterLogManager":
    from dagster._core.log_manager import DagsterLogManager

    # initialize default colored console logger
    loggers = []
    for logger_def, logger_config in default_system_loggers(instance):
        loggers.append(
            logger_def.logger_fn(
                InitLoggerContext(
                    logger_config, logger_def, run_id=dagster_run.run_id if dagster_run else None
                )
            )
        )
    return DagsterLogManager.create(loggers=loggers, dagster_run=dagster_run, instance=instance)


# This represents all the data that is passed *into* context creation process.
# The remainder of the objects generated (e.g. loggers, resources) are created
# using user-defined code that may fail at runtime and result in the emission
# of a pipeline init failure events. The data in this object are passed all
# over the place during the context creation process so grouping here for
# ease of argument passing etc.
class ContextCreationData(NamedTuple):
    job: IJob
    resolved_run_config: ResolvedRunConfig
    dagster_run: DagsterRun
    executor_def: ExecutorDefinition
    instance: DagsterInstance
    resource_keys_to_init: AbstractSet[str]
    execution_plan: ExecutionPlan

    @property
    def job_def(self) -> JobDefinition:
        return self.job.get_definition()

    @property
    def repository_def(self) -> Optional[RepositoryDefinition]:
        return self.job.get_repository_definition()


def create_context_creation_data(
    job: IJob,
    execution_plan: ExecutionPlan,
    run_config: Mapping[str, object],
    dagster_run: DagsterRun,
    instance: DagsterInstance,
) -> "ContextCreationData":
    job_def = job.get_definition()
    resolved_run_config = ResolvedRunConfig.build(job_def, run_config)

    executor_def = job_def.executor_def

    return ContextCreationData(
        job=job,
        resolved_run_config=resolved_run_config,
        dagster_run=dagster_run,
        executor_def=executor_def,
        instance=instance,
        resource_keys_to_init=get_required_resource_keys_to_init(execution_plan, job_def),
        execution_plan=execution_plan,
    )


def create_plan_data(
    context_creation_data: "ContextCreationData",
    raise_on_error: bool,
    retry_mode: RetryMode,
    step_dependency_config: StepDependencyConfig,
) -> PlanData:
    return PlanData(
        job=context_creation_data.job,
        dagster_run=context_creation_data.dagster_run,
        instance=context_creation_data.instance,
        execution_plan=context_creation_data.execution_plan,
        raise_on_error=raise_on_error,
        retry_mode=retry_mode,
        step_dependency_config=step_dependency_config,
    )


def create_execution_data(
    context_creation_data: "ContextCreationData",
    scoped_resources_builder: ScopedResourcesBuilder,
) -> ExecutionData:
    return ExecutionData(
        scoped_resources_builder=scoped_resources_builder,
        resolved_run_config=context_creation_data.resolved_run_config,
        job_def=context_creation_data.job_def,
        repository_def=context_creation_data.repository_def,
    )


TContextType = TypeVar("TContextType", bound=IPlanContext)


class ExecutionContextManager(Generic[TContextType], ABC):
    def __init__(
        self,
        event_generator: Iterator[Union[DagsterEvent, TContextType]],
        raise_on_error: Optional[bool] = False,
    ):
        self._manager = EventGenerationManager[TContextType](
            generator=event_generator, object_cls=self.context_type, require_object=raise_on_error
        )

    @property
    @abstractmethod
    def context_type(self) -> type[TContextType]:
        pass

    def prepare_context(self) -> Iterable[DagsterEvent]:  # ode to Preparable
        return self._manager.generate_setup_events()

    def get_context(self) -> TContextType:
        return self._manager.get_object()

    def shutdown_context(self) -> Iterable[DagsterEvent]:
        return self._manager.generate_teardown_events()

    def get_generator(self) -> Generator[Union[DagsterEvent, IPlanContext], None, None]:
        return self._manager.generator


def execution_context_event_generator(
    job: IJob,
    execution_plan: ExecutionPlan,
    run_config: Mapping[str, object],
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    retry_mode: RetryMode,
    scoped_resources_builder_cm: Optional[
        Callable[..., EventGenerationManager[ScopedResourcesBuilder]]
    ] = None,
    raise_on_error: Optional[bool] = False,
    output_capture: Optional[dict["StepOutputHandle", Any]] = None,
    step_dependency_config: StepDependencyConfig = StepDependencyConfig.default(),
) -> Generator[Union[DagsterEvent, PlanExecutionContext], None, None]:
    scoped_resources_builder_cm = cast(
        "Callable[..., EventGenerationManager[ScopedResourcesBuilder]]",
        check.opt_callable_param(
            scoped_resources_builder_cm,
            "scoped_resources_builder_cm",
            default=resource_initialization_manager,
        ),
    )

    execution_plan = check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    job_def = job.get_definition()

    run_config = check.mapping_param(run_config, "run_config", key_type=str)
    dagster_run = check.inst_param(dagster_run, "dagster_run", DagsterRun)
    instance = check.inst_param(instance, "instance", DagsterInstance)

    raise_on_error = check.bool_param(raise_on_error, "raise_on_error")

    context_creation_data = create_context_creation_data(
        job,
        execution_plan,
        run_config,
        dagster_run,
        instance,
    )

    log_manager = create_log_manager(context_creation_data)
    resource_defs = job_def.get_required_resource_defs()
    event_loop = asyncio.new_event_loop()
    try:
        resources_manager = scoped_resources_builder_cm(
            resource_defs=resource_defs,
            resource_configs=context_creation_data.resolved_run_config.resources,
            log_manager=log_manager,
            execution_plan=execution_plan,
            dagster_run=context_creation_data.dagster_run,
            resource_keys_to_init=context_creation_data.resource_keys_to_init,
            instance=instance,
            emit_persistent_events=True,
            event_loop=event_loop,
        )
        yield from resources_manager.generate_setup_events()
        scoped_resources_builder = check.inst(
            resources_manager.get_object(), ScopedResourcesBuilder
        )

        execution_context = PlanExecutionContext(
            plan_data=create_plan_data(
                context_creation_data,
                raise_on_error,
                retry_mode,
                step_dependency_config,
            ),
            execution_data=create_execution_data(context_creation_data, scoped_resources_builder),
            log_manager=log_manager,
            output_capture=output_capture,
            event_loop=event_loop,
        )

        _validate_plan_with_context(execution_context, execution_plan)

        yield execution_context
        yield from resources_manager.generate_teardown_events()

    finally:
        try:
            # If are running in another active event loop than this cleanup
            # will throw RuntimeError('Cannot run the event loop while another loop is running')
            # There is no public API that does not throw to check for this condition, so just run
            # the cleanup and ignore the exception.
            event_loop.run_until_complete(event_loop.shutdown_asyncgens())
        except RuntimeError:
            pass

        event_loop.close()


class PlanOrchestrationContextManager(ExecutionContextManager[PlanOrchestrationContext]):
    def __init__(
        self,
        context_event_generator: Callable[
            ...,
            Iterator[Union[DagsterEvent, PlanOrchestrationContext]],
        ],
        job: IJob,
        execution_plan: ExecutionPlan,
        run_config: Mapping[str, object],
        dagster_run: DagsterRun,
        instance: DagsterInstance,
        raise_on_error: Optional[bool] = False,
        output_capture: Optional[dict["StepOutputHandle", Any]] = None,
        executor_defs: Optional[Sequence[ExecutorDefinition]] = None,
        resume_from_failure=False,
    ):
        event_generator = context_event_generator(
            job,
            execution_plan,
            run_config,
            dagster_run,
            instance,
            raise_on_error,
            executor_defs,
            output_capture,
            resume_from_failure=resume_from_failure,
        )
        super().__init__(event_generator)

    @property
    def context_type(self) -> type[PlanOrchestrationContext]:
        return PlanOrchestrationContext


def orchestration_context_event_generator(
    job: IJob,
    execution_plan: ExecutionPlan,
    run_config: Mapping[str, object],
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    raise_on_error: bool,
    executor_defs: Optional[Sequence[ExecutorDefinition]],
    output_capture: Optional[dict["StepOutputHandle", Any]],
    resume_from_failure: bool = False,
) -> Iterator[Union[DagsterEvent, PlanOrchestrationContext]]:
    check.invariant(executor_defs is None)
    context_creation_data = create_context_creation_data(
        job,
        execution_plan,
        run_config,
        dagster_run,
        instance,
    )

    log_manager = create_log_manager(context_creation_data)

    try:
        executor = create_executor(context_creation_data)

        execution_context = PlanOrchestrationContext(
            plan_data=create_plan_data(
                context_creation_data,
                raise_on_error,
                executor.retries,
                executor.step_dependency_config,
            ),
            log_manager=log_manager,
            executor=executor,
            output_capture=output_capture,
            resume_from_failure=resume_from_failure,
        )

        _validate_plan_with_context(execution_context, execution_plan)

        yield execution_context
    except DagsterError as dagster_error:
        dagster_error = cast("DagsterUserCodeExecutionError", dagster_error)
        user_facing_exc_info = (
            # pylint does not know original_exc_info exists is is_user_code_error is true
            dagster_error.original_exc_info if dagster_error.is_user_code_error else sys.exc_info()
        )
        error_info = serializable_error_info_from_exc_info(user_facing_exc_info)

        event = DagsterEvent.job_failure(
            job_context_or_name=dagster_run.job_name,
            context_msg=(
                "Failure during initialization for job"
                f' "{dagster_run.job_name}". This may be due to a failure in initializing the'
                " executor or one of the loggers."
            ),
            failure_reason=RunFailureReason.JOB_INITIALIZATION_FAILURE,
            error_info=error_info,
        )
        log_manager.log_dagster_event(
            level=logging.ERROR, msg=event.message or "", dagster_event=event
        )
        yield event

        if raise_on_error:
            raise dagster_error


class PlanExecutionContextManager(ExecutionContextManager[PlanExecutionContext]):
    def __init__(
        self,
        job: IJob,
        execution_plan: ExecutionPlan,
        run_config: Mapping[str, object],
        dagster_run: DagsterRun,
        instance: DagsterInstance,
        retry_mode: RetryMode,
        scoped_resources_builder_cm: Optional[
            Callable[..., EventGenerationManager[ScopedResourcesBuilder]]
        ] = None,
        raise_on_error: Optional[bool] = False,
        output_capture: Optional[dict["StepOutputHandle", Any]] = None,
        step_dependency_config: StepDependencyConfig = StepDependencyConfig.default(),
    ):
        super().__init__(
            execution_context_event_generator(
                job,
                execution_plan,
                run_config,
                dagster_run,
                instance,
                retry_mode,
                scoped_resources_builder_cm,
                raise_on_error=raise_on_error,
                output_capture=output_capture,
                step_dependency_config=step_dependency_config,
            )
        )

    @property
    def context_type(self) -> type[PlanExecutionContext]:
        return PlanExecutionContext


# perform any plan validation that is dependent on access to the pipeline context
def _validate_plan_with_context(job_context: IPlanContext, execution_plan: ExecutionPlan) -> None:
    validate_reexecution_memoization(job_context, execution_plan)


def create_executor(context_creation_data: ContextCreationData) -> "Executor":
    check.inst_param(context_creation_data, "context_creation_data", ContextCreationData)
    init_context = InitExecutorContext(
        job=context_creation_data.job,
        executor_def=context_creation_data.executor_def,
        executor_config=context_creation_data.resolved_run_config.execution.execution_engine_config,
        instance=context_creation_data.instance,
    )
    check_cross_process_constraints(init_context)
    creation_fn = check.not_none(context_creation_data.executor_def.executor_creation_fn)
    return creation_fn(init_context)


@contextmanager
def scoped_job_context(
    execution_plan: ExecutionPlan,
    job: IJob,
    run_config: Mapping[str, object],
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    scoped_resources_builder_cm: Callable[
        ..., EventGenerationManager[ScopedResourcesBuilder]
    ] = resource_initialization_manager,
    raise_on_error: Optional[bool] = False,
) -> Generator[PlanExecutionContext, None, None]:
    """Utility context manager which acts as a very thin wrapper around
    `pipeline_initialization_manager`, iterating through all the setup/teardown events and
    discarding them.  It yields the resulting `pipeline_context`.

    Should only be used where we need to reconstruct the pipeline context, ignoring any yielded
    events (e.g. JobExecutionResult, dagstermill, unit tests, etc)
    """
    check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
    check.inst_param(job, "job", IJob)
    check.mapping_param(run_config, "run_config", key_type=str)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)
    check.inst_param(instance, "instance", DagsterInstance)
    check.callable_param(scoped_resources_builder_cm, "scoped_resources_builder_cm")

    initialization_manager = PlanExecutionContextManager(
        job,
        execution_plan,
        run_config,
        dagster_run,
        instance,
        RetryMode.DISABLED,
        scoped_resources_builder_cm=scoped_resources_builder_cm,
        raise_on_error=raise_on_error,
    )
    for _ in initialization_manager.prepare_context():
        pass

    try:
        yield check.inst(initialization_manager.get_context(), PlanExecutionContext)
    finally:
        for _ in initialization_manager.shutdown_context():
            pass


def create_log_manager(
    context_creation_data: ContextCreationData,
) -> "DagsterLogManager":
    from dagster._core.log_manager import DagsterLogManager

    check.inst_param(context_creation_data, "context_creation_data", ContextCreationData)

    job_def, resolved_run_config, dagster_run = (
        context_creation_data.job_def,
        context_creation_data.resolved_run_config,
        context_creation_data.dagster_run,
    )

    # The following logic is tightly coupled to the processing of logger config in
    # python_modules/dagster/dagster/_core/system_config/objects.py#config_map_loggers
    # Changes here should be accompanied checked against that function, which applies config mapping
    # via ConfigurableDefinition (@configured) to incoming logger configs. See docstring for more details.

    loggers = []
    for logger_key, logger_def in job_def.loggers.items() or default_loggers().items():
        if logger_key in resolved_run_config.loggers:
            loggers.append(
                logger_def.logger_fn(
                    InitLoggerContext(
                        resolved_run_config.loggers.get(logger_key, {}).get("config"),
                        logger_def,
                        job_def=job_def,
                        run_id=dagster_run.run_id,
                    )
                )
            )

    if not loggers:
        for logger_def, logger_config in default_system_loggers(context_creation_data.instance):
            loggers.append(
                logger_def.logger_fn(
                    InitLoggerContext(
                        logger_config,
                        logger_def,
                        job_def=job_def,
                        run_id=dagster_run.run_id,
                    )
                )
            )

    return DagsterLogManager.create(
        loggers=loggers, dagster_run=dagster_run, instance=context_creation_data.instance
    )


def create_context_free_log_manager(
    instance: DagsterInstance, dagster_run: DagsterRun
) -> "DagsterLogManager":
    """In the event of pipeline initialization failure, we want to be able to log the failure
    without a dependency on the PlanExecutionContext to initialize DagsterLogManager.

    Args:
        dagster_run (PipelineRun)
        pipeline_def (JobDefinition)
    """
    from dagster._core.log_manager import DagsterLogManager

    check.inst_param(instance, "instance", DagsterInstance)
    check.inst_param(dagster_run, "dagster_run", DagsterRun)

    loggers = []
    # Use the default logger
    for logger_def, logger_config in default_system_loggers(instance):
        loggers += [
            logger_def.logger_fn(
                InitLoggerContext(
                    logger_config,
                    logger_def,
                    job_def=None,
                    run_id=dagster_run.run_id,
                )
            )
        ]

    return DagsterLogManager.create(loggers=loggers, instance=instance, dagster_run=dagster_run)
