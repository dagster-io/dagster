from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    cast,
)

from dagster import _check as check
from dagster._core.events import DagsterEvent
from dagster._core.execution.context.system import IStepContext, PlanOrchestrationContext
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.executor.step_delegating.step_delegating_executor import StepDelegatingExecutor
from dagster._core.executor.step_delegating.step_handler.base import (
    CheckStepHealthResult,
    StepHandler,
    StepHandlerContext,
)


def step_context_for_handler_context(step_handler_context: StepHandlerContext) -> IStepContext:
    step_keys = step_handler_context.step_keys
    check.invariant(len(step_keys) == 1)
    return step_handler_context.get_step_context(step_keys[0])


class StepHandlerForPerStepExecutor(StepHandler):
    def __init__(
        self,
        step_executor_factory: Callable[[StepHandlerContext, IStepContext], "StepExecutor"],
    ):
        self._step_executor_factory = step_executor_factory
        self._step_executors: Dict[str, StepExecutor] = {}

    @property
    def name(self) -> str:
        return "StepHandlerForPerStepExecutor"

    def _get_step_executor(self, step_handler_context: StepHandlerContext) -> "StepExecutor":
        step_context = step_context_for_handler_context(step_handler_context)
        step_key = step_context.step.key
        if step_key not in self._step_executors:
            self._step_executors[step_key] = self._step_executor_factory(
                step_handler_context, step_context
            )
        return self._step_executors[step_key]

    def launch_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        step_executor = self._get_step_executor(step_handler_context)
        step_context = step_executor.step_context
        yield DagsterEvent.step_worker_starting(
            step_context,
            message=f'Executing step "{step_context.step.key}" in external process',
            metadata_entries=[],
        )

        iterator = step_executor.execute()
        if iterator:
            yield from iterator

    @property
    def step_executors(self) -> Mapping[str, "StepExecutor"]:
        return self._step_executors

    def check_step_health(self, step_handler_context: StepHandlerContext) -> CheckStepHealthResult:
        return self._get_step_executor(step_handler_context).check_step_health()

    def terminate_step(self, step_handler_context: StepHandlerContext) -> Iterator[DagsterEvent]:
        iterator = self._get_step_executor(step_handler_context).terminate()
        if iterator:
            yield from iterator


class StepExecutor(ABC):
    def __init__(self, step_handler_context: StepHandlerContext, step_context: IStepContext):
        # Users will inherit from this so doing runtime checks
        self.step_handler_context = check.inst_param(
            step_handler_context, "step_handler_context", StepHandlerContext
        )
        self.step_context = check.inst_param(step_context, "step_context", IStepContext)

    @property
    def step_key(self) -> str:
        return self.step_context.step.key

    @abstractmethod
    def execute(self) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    @abstractmethod
    def terminate(self) -> Optional[Iterator[DagsterEvent]]:
        raise NotImplementedError()

    @abstractmethod
    def check_step_health(self) -> CheckStepHealthResult:
        raise NotImplementedError()


class StepExecutorBasedExecutor(Executor):
    @property
    def step_count(self) -> int:
        return len(self.step_executors)

    @property
    @abstractmethod
    def step_executors(self) -> Mapping[str, "StepExecutor"]:
        ...


class PluggableStepExecutorBasedRunExecutor(StepExecutorBasedExecutor):
    def __init__(
        self,
        step_executor_factory: Callable[[StepHandlerContext, IStepContext], "StepExecutor"],
        retries: RetryMode,
        sleep_seconds: Optional[float] = None,
        check_step_health_interval_seconds: Optional[int] = None,
        max_concurrent: Optional[int] = None,
        tag_concurrency_limits: Optional[List[Dict[str, Any]]] = None,
        should_verify_step: bool = False,
    ):
        self._step_handler = StepHandlerForPerStepExecutor(step_executor_factory)
        self._inner_executor = StepDelegatingExecutor(
            step_handler=self._step_handler,
            retries=retries,
            sleep_seconds=sleep_seconds,
            check_step_health_interval_seconds=check_step_health_interval_seconds,
            max_concurrent=max_concurrent,
            tag_concurrency_limits=tag_concurrency_limits,
            should_verify_step=should_verify_step,
        )

    def execute(self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan):
        return self._inner_executor.execute(plan_context, execution_plan)

    @property
    def retries(self) -> RetryMode:
        return self._inner_executor.retries

    @property
    def step_executors(self) -> Mapping[str, "StepExecutor"]:
        return self._step_handler.step_executors


TStepExecutor = TypeVar("TStepExecutor", bound=StepExecutor)


class GenericRunExecutor(StepExecutorBasedExecutor, Generic[TStepExecutor]):
    def _create_step_executor(
        self, step_handler_context: StepHandlerContext, step_context: IStepContext
    ) -> TStepExecutor:
        return self._step_executor_cls(step_handler_context, step_context)

    def __init__(
        self,
        # from https://stackoverflow.com/a/70231012
        # This seems to be the most reliable way to be able to access the generic type parameter at runtime
        # Requires type as first parameter rather than as generic type parameter
        step_executor_cls: Type[TStepExecutor],
        retries: RetryMode,
        sleep_seconds: Optional[float] = None,
        check_step_health_interval_seconds: Optional[int] = None,
        max_concurrent: Optional[int] = None,
        tag_concurrency_limits: Optional[List[Dict[str, Any]]] = None,
        should_verify_step: bool = False,
    ):
        self._step_executor_cls = step_executor_cls
        self._inner_executor = PluggableStepExecutorBasedRunExecutor(
            self._create_step_executor,
            retries=retries,
            sleep_seconds=sleep_seconds,
            check_step_health_interval_seconds=check_step_health_interval_seconds,
            max_concurrent=max_concurrent,
            tag_concurrency_limits=tag_concurrency_limits,
            should_verify_step=should_verify_step,
        )

    def execute(self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan):
        return self._inner_executor.execute(plan_context, execution_plan)

    @property
    def retries(self) -> RetryMode:
        return self._inner_executor.retries

    @property
    def step_executors(self) -> Mapping[str, TStepExecutor]:
        return cast(Mapping[str, TStepExecutor], self._inner_executor._step_handler.step_executors)
