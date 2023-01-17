import copy
import logging
from contextlib import ExitStack
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
)

import pendulum
from typing_extensions import TypeAlias, TypeGuard

import dagster._check as check
from dagster._annotations import public
from dagster._core.definitions.instigation_logger import InstigationLogger
from dagster._serdes import whitelist_for_serdes
from dagster._utils import ensure_gen
from dagster._utils.merger import merge_dicts
from dagster._utils.schedules import is_valid_cron_schedule

from ..decorator_utils import get_function_params
from ..errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from ..instance import DagsterInstance
from ..instance.ref import InstanceRef
from ..storage.pipeline_run import DagsterRun
from .graph_definition import GraphDefinition
from .mode import DEFAULT_MODE_NAME
from .pipeline_definition import PipelineDefinition
from .run_request import RunRequest, SkipReason
from .target import DirectTarget, ExecutableDefinition, RepoRelativeTarget
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from .utils import check_valid_name, validate_tags

T = TypeVar("T")

RunConfig: TypeAlias = Mapping[str, Any]
RunRequestIterator: TypeAlias = Iterator[Union[RunRequest, SkipReason]]

ScheduleEvaluationFunctionReturn: TypeAlias = Union[
    RunRequest, SkipReason, RunConfig, RunRequestIterator, Sequence[RunRequest]
]
RawScheduleEvaluationFunction: TypeAlias = Union[
    Callable[["ScheduleEvaluationContext"], ScheduleEvaluationFunctionReturn],
    Callable[[], ScheduleEvaluationFunctionReturn],
]

ScheduleRunConfigFunction: TypeAlias = Union[
    Callable[["ScheduleEvaluationContext"], RunConfig],
    Callable[[], RunConfig],
]

ScheduleTagsFunction: TypeAlias = Callable[["ScheduleEvaluationContext"], Mapping[str, str]]
ScheduleShouldExecuteFunction: TypeAlias = Callable[["ScheduleEvaluationContext"], bool]
ScheduleExecutionFunction: TypeAlias = Union[
    Callable[["ScheduleEvaluationContext"], Any],
    "DecoratedScheduleFunction",
]


@whitelist_for_serdes
class DefaultScheduleStatus(Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class ScheduleEvaluationContext:
    """The context object available as the first argument various functions defined on a :py:class:`dagster.ScheduleDefinition`.

    A `ScheduleEvaluationContext` object is passed as the first argument to ``run_config_fn``, ``tags_fn``,
    and ``should_execute``.

    Users should not instantiate this object directly. To construct a `ScheduleEvaluationContext` for testing purposes, use :py:func:`dagster.build_schedule_context`.

    Attributes:
        instance_ref (Optional[InstanceRef]): The serialized instance configured to run the schedule
        scheduled_execution_time (datetime):
            The time in which the execution was scheduled to happen. May differ slightly
            from both the actual execution time and the time at which the run config is computed.
            Not available in all schedulers - currently only set in deployments using
            DagsterDaemonScheduler.

    Example:

    .. code-block:: python

        from dagster import schedule, ScheduleEvaluationContext

        @schedule
        def the_schedule(context: ScheduleEvaluationContext):
            ...

    """

    __slots__ = [
        "_instance_ref",
        "_scheduled_execution_time",
        "_exit_stack",
        "_instance",
        "_log_key",
        "_logger",
        "_repository_name",
        "_schedule_name",
    ]

    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
        scheduled_execution_time: Optional[datetime],
        repository_name: Optional[str] = None,
        schedule_name: Optional[str] = None,
    ):
        self._exit_stack = ExitStack()
        self._instance = None

        self._instance_ref = check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
        self._scheduled_execution_time = check.opt_inst_param(
            scheduled_execution_time, "scheduled_execution_time", datetime
        )
        self._log_key = (
            [
                repository_name,
                schedule_name,
                scheduled_execution_time.strftime("%Y%m%d_%H%M%S"),
            ]
            if repository_name and schedule_name and scheduled_execution_time
            else None
        )
        self._logger = None
        self._repository_name = repository_name
        self._schedule_name = schedule_name

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()
        self._logger = None

    @public  # type: ignore
    @property
    def instance(self) -> "DagsterInstance":
        # self._instance_ref should only ever be None when this ScheduleEvaluationContext was
        # constructed under test.
        if not self._instance_ref:
            raise DagsterInvariantViolationError(
                "Attempted to initialize dagster instance, but no instance reference was provided."
            )
        if not self._instance:
            self._instance = self._exit_stack.enter_context(
                DagsterInstance.from_ref(self._instance_ref)
            )
        return cast(DagsterInstance, self._instance)

    @public  # type: ignore
    @property
    def scheduled_execution_time(self) -> Optional[datetime]:
        return self._scheduled_execution_time

    @property
    def log(self) -> logging.Logger:
        if self._logger:
            return self._logger

        if not self._instance_ref:
            self._logger = self._exit_stack.enter_context(
                InstigationLogger(
                    self._log_key,
                    repository_name=self._repository_name,
                    name=self._schedule_name,
                )
            )

        self._logger = self._exit_stack.enter_context(
            InstigationLogger(
                self._log_key,
                self.instance,
                repository_name=self._repository_name,
                name=self._schedule_name,
            )
        )
        return cast(InstigationLogger, self._logger)

    def has_captured_logs(self):
        return self._logger and self._logger.has_captured_logs()

    @property
    def log_key(self) -> Optional[List[str]]:
        return self._log_key


class DecoratedScheduleFunction(NamedTuple):
    """Wrapper around the decorated schedule function.  Keeps track of both to better support the
    optimal return value for direct invocation of the evaluation function.
    """

    decorated_fn: RawScheduleEvaluationFunction
    wrapped_fn: Callable[[ScheduleEvaluationContext], RunRequestIterator]
    has_context_arg: bool


def is_context_provided(
    fn: Union[Callable[[ScheduleEvaluationContext], T], Callable[[], T]]
) -> TypeGuard[Callable[[ScheduleEvaluationContext], T]]:
    return len(get_function_params(fn)) == 1


def build_schedule_context(
    instance: Optional[DagsterInstance] = None, scheduled_execution_time: Optional[datetime] = None
) -> ScheduleEvaluationContext:
    """Builds schedule execution context using the provided parameters.

    The instance provided to ``build_schedule_context`` must be persistent;
    DagsterInstance.ephemeral() will result in an error.

    Args:
        instance (Optional[DagsterInstance]): The dagster instance configured to run the schedule.
        scheduled_execution_time (datetime): The time in which the execution was scheduled to
            happen. May differ slightly from both the actual execution time and the time at which
            the run config is computed.

    Examples:
        .. code-block:: python

            context = build_schedule_context(instance)
            daily_schedule.evaluate_tick(context)

    """
    check.opt_inst_param(instance, "instance", DagsterInstance)
    return ScheduleEvaluationContext(
        instance_ref=instance.get_ref() if instance and instance.is_persistent else None,
        scheduled_execution_time=check.opt_inst_param(
            scheduled_execution_time, "scheduled_execution_time", datetime
        ),
    )


@whitelist_for_serdes
class ScheduleExecutionData(
    NamedTuple(
        "_ScheduleExecutionData",
        [
            ("run_requests", Optional[Sequence[RunRequest]]),
            ("skip_message", Optional[str]),
            ("captured_log_key", Optional[Sequence[str]]),
        ],
    )
):
    def __new__(
        cls,
        run_requests: Optional[Sequence[RunRequest]] = None,
        skip_message: Optional[str] = None,
        captured_log_key: Optional[Sequence[str]] = None,
    ):
        check.opt_sequence_param(run_requests, "run_requests", RunRequest)
        check.opt_str_param(skip_message, "skip_message")
        check.opt_list_param(captured_log_key, "captured_log_key", str)
        check.invariant(
            not (run_requests and skip_message), "Found both skip data and run request data"
        )
        return super(ScheduleExecutionData, cls).__new__(
            cls,
            run_requests=run_requests,
            skip_message=skip_message,
            captured_log_key=captured_log_key,
        )


class ScheduleDefinition:
    """Define a schedule that targets a job.

    Args:
        name (Optional[str]): The name of the schedule to create. Defaults to the job name plus
            "_schedule".
        cron_schedule (Union[str, Sequence[str]]): A valid cron string or sequence of cron strings
            specifying when the schedule will run, e.g., ``'45 23 * * 6'`` for a schedule that runs
            at 11:45 PM every Saturday. If a sequence is provided, then the schedule will run for
            the union of all execution times for the provided cron strings, e.g.,
            ``['45 23 * * 6', '30 9 * * 0]`` for a schedule that runs at 11:45 PM every Saturday and
            9:30 AM every Sunday.
        execution_fn (Callable[ScheduleEvaluationContext]): The core evaluation function for the
            schedule, which is run at an interval to determine whether a run should be launched or
            not. Takes a :py:class:`~dagster.ScheduleEvaluationContext`.

            This function must return a generator, which must yield either a single SkipReason
            or one or more RunRequest objects.
        run_config (Optional[Mapping]): The config that parameterizes this execution,
            as a dict.
        run_config_fn (Optional[Callable[[ScheduleEvaluationContext], [Mapping]]]): A function that
            takes a ScheduleEvaluationContext object and returns the run configuration that
            parameterizes this execution, as a dict. You may set only one of ``run_config``,
            ``run_config_fn``, and ``execution_fn``.
        tags (Optional[Mapping[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the scheduled runs.
        tags_fn (Optional[Callable[[ScheduleEvaluationContext], Optional[Mapping[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes a
            :py:class:`~dagster.ScheduleEvaluationContext` and returns a dictionary of tags (string
            key-value pairs). You may set only one of ``tags``, ``tags_fn``, and ``execution_fn``.
        should_execute (Optional[Callable[[ScheduleEvaluationContext], bool]]): A function that runs
            at schedule execution time to determine whether a schedule should execute or skip. Takes
            a :py:class:`~dagster.ScheduleEvaluationContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        environment_vars (Optional[dict[str, str]]): The environment variables to set for the
            schedule
        execution_timezone (Optional[str]): Timezone in which the schedule should run.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        description (Optional[str]): A human-readable description of the schedule.
        job (Optional[Union[GraphDefinition, JobDefinition]]): The job that should execute when this
            schedule runs.
        default_status (DefaultScheduleStatus): Whether the schedule starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        *,
        cron_schedule: Optional[Union[str, Sequence[str]]] = None,
        job_name: Optional[str] = None,
        run_config: Optional[Any] = None,
        run_config_fn: Optional[ScheduleRunConfigFunction] = None,
        tags: Optional[Mapping[str, str]] = None,
        tags_fn: Optional[ScheduleTagsFunction] = None,
        should_execute: Optional[ScheduleShouldExecuteFunction] = None,
        environment_vars: Optional[Mapping[str, str]] = None,
        execution_timezone: Optional[str] = None,
        execution_fn: Optional[ScheduleExecutionFunction] = None,
        description: Optional[str] = None,
        job: Optional[ExecutableDefinition] = None,
        default_status: DefaultScheduleStatus = DefaultScheduleStatus.STOPPED,
    ):
        self._cron_schedule = check.inst_param(cron_schedule, "cron_schedule", (str, Sequence))
        if not isinstance(self._cron_schedule, str):
            check.sequence_param(self._cron_schedule, "cron_schedule", of_type=str)  # type: ignore

        if not is_valid_cron_schedule(self._cron_schedule):  # type: ignore
            raise DagsterInvalidDefinitionError(
                f"Found invalid cron schedule '{self._cron_schedule}' for schedule '{name}''. "
                "Dagster recognizes standard cron expressions consisting of 5 fields."
            )

        if job is not None:
            self._target: Union[DirectTarget, RepoRelativeTarget] = DirectTarget(job)
        else:
            self._target = RepoRelativeTarget(
                pipeline_name=check.str_param(job_name, "job_name"),
                mode=DEFAULT_MODE_NAME,
                solid_selection=None,
            )

        if name:
            self._name = check_valid_name(name)
        elif job_name:
            self._name = job_name + "_schedule"
        elif job:
            self._name = job.name + "_schedule"

        self._description = check.opt_str_param(description, "description")

        self._environment_vars = check.opt_mapping_param(
            environment_vars, "environment_vars", key_type=str, value_type=str
        )
        self._execution_timezone = check.opt_str_param(execution_timezone, "execution_timezone")

        if execution_fn and (run_config_fn or tags_fn or should_execute or tags or run_config):
            raise DagsterInvalidDefinitionError(
                "Attempted to provide both execution_fn and individual run_config/tags arguments "
                "to ScheduleDefinition. Must provide only one of the two."
            )
        elif execution_fn:
            self._execution_fn: Optional[
                Union[Callable[..., Any], DecoratedScheduleFunction]
            ] = None
            if isinstance(execution_fn, DecoratedScheduleFunction):
                self._execution_fn = execution_fn
            else:
                self._execution_fn = check.opt_callable_param(execution_fn, "execution_fn")
            self._run_config_fn = None
        else:
            if run_config_fn and run_config:
                raise DagsterInvalidDefinitionError(
                    "Attempted to provide both run_config_fn and run_config as arguments"
                    " to ScheduleDefinition. Must provide only one of the two."
                )

            # pylint: disable=unused-argument
            def _default_run_config_fn(context: ScheduleEvaluationContext) -> RunConfig:
                return check.opt_dict_param(run_config, "run_config")

            self._run_config_fn = check.opt_callable_param(
                run_config_fn, "run_config_fn", default=_default_run_config_fn
            )

            if tags_fn and tags:
                raise DagsterInvalidDefinitionError(
                    "Attempted to provide both tags_fn and tags as arguments"
                    " to ScheduleDefinition. Must provide only one of the two."
                )
            elif tags:
                tags = validate_tags(tags, allow_reserved_tags=False)
                tags_fn = lambda _context: tags  # type: ignore
            else:
                tags_fn = check.opt_callable_param(
                    tags_fn, "tags_fn", default=lambda _context: cast(Mapping[str, str], {})
                )

            _should_execute: ScheduleShouldExecuteFunction = check.opt_callable_param(
                should_execute, "should_execute", default=lambda _context: True
            )

            # Several type-ignores are present in this function to work around bugs in mypy
            # inference.
            def _execution_fn(context: ScheduleEvaluationContext) -> RunRequestIterator:
                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of should_execute for schedule {name}",
                ):
                    if not _should_execute(context):
                        yield SkipReason(
                            "should_execute function for {schedule_name} returned false.".format(
                                schedule_name=name
                            )
                        )
                        return

                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of run_config_fn for schedule {name}",
                ):
                    _run_config_fn = check.not_none(self._run_config_fn)
                    evaluated_run_config = copy.deepcopy(
                        _run_config_fn(context)
                        if is_context_provided(_run_config_fn)  # type: ignore
                        else run_config_fn()  # type: ignore
                    )

                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of tags_fn for schedule {name}",
                ):
                    evaluated_tags = validate_tags(tags_fn(context), allow_reserved_tags=False)  # type: ignore

                yield RunRequest(
                    run_key=None,
                    run_config=evaluated_run_config,  # type: ignore
                    tags=evaluated_tags,
                )

            self._execution_fn = _execution_fn

        if self._execution_timezone:
            try:
                # Verify that the timezone can be loaded
                pendulum.tz.timezone(self._execution_timezone)
            except Exception as e:
                raise DagsterInvalidDefinitionError(
                    f"Invalid execution timezone {self._execution_timezone} for {name}"
                ) from e

        self._default_status = check.inst_param(
            default_status, "default_status", DefaultScheduleStatus
        )

    def __call__(self, *args, **kwargs):
        from .decorators.schedule_decorator import DecoratedScheduleFunction

        if not isinstance(self._execution_fn, DecoratedScheduleFunction):
            raise DagsterInvalidInvocationError(
                "Schedule invocation is only supported for schedules created via the schedule "
                "decorators."
            )
        result = None
        if self._execution_fn.has_context_arg:
            if len(args) == 0 and len(kwargs) == 0:
                raise DagsterInvalidInvocationError(
                    "Schedule decorated function has context argument, but no context argument was "
                    "provided when invoking."
                )
            if len(args) + len(kwargs) > 1:
                raise DagsterInvalidInvocationError(
                    "Schedule invocation received multiple arguments. Only a first "
                    "positional context parameter should be provided when invoking."
                )

            context_param_name = get_function_params(self._execution_fn.decorated_fn)[0].name

            if args:
                context = check.opt_inst_param(
                    args[0], context_param_name, ScheduleEvaluationContext
                )
            else:
                if context_param_name not in kwargs:
                    raise DagsterInvalidInvocationError(
                        f"Schedule invocation expected argument '{context_param_name}'."
                    )
                context = check.opt_inst_param(
                    kwargs[context_param_name], context_param_name, ScheduleEvaluationContext
                )

            context = context if context else build_schedule_context()

            result = self._execution_fn.decorated_fn(context)  # type: ignore
        else:
            if len(args) + len(kwargs) > 0:
                raise DagsterInvalidInvocationError(
                    "Decorated schedule function takes no arguments, but arguments were provided."
                )
            result = self._execution_fn.decorated_fn()  # type: ignore

        if isinstance(result, dict):
            return copy.deepcopy(result)
        else:
            return result

    @public  # type: ignore
    @property
    def name(self) -> str:
        return self._name

    @public  # type: ignore
    @property
    def job_name(self) -> str:
        return self._target.pipeline_name

    @public  # type: ignore
    @property
    def description(self) -> Optional[str]:
        return self._description

    @public  # type: ignore
    @property
    def cron_schedule(self) -> Union[str, Sequence[str]]:
        return self._cron_schedule  # type: ignore

    @public  # type: ignore
    @property
    def environment_vars(self) -> Mapping[str, str]:
        return self._environment_vars

    @public  # type: ignore
    @property
    def execution_timezone(self) -> Optional[str]:
        return self._execution_timezone

    @public  # type: ignore
    @property
    def job(self) -> Union[GraphDefinition, PipelineDefinition, UnresolvedAssetJobDefinition]:
        if isinstance(self._target, DirectTarget):
            return self._target.target
        raise DagsterInvalidDefinitionError("No job was provided to ScheduleDefinition.")

    def evaluate_tick(self, context: "ScheduleEvaluationContext") -> ScheduleExecutionData:
        """Evaluate schedule using the provided context.

        Args:
            context (ScheduleEvaluationContext): The context with which to evaluate this schedule.

        Returns:
            ScheduleExecutionData: Contains list of run requests, or skip message if present.

        """
        check.inst_param(context, "context", ScheduleEvaluationContext)
        execution_fn: Callable[[ScheduleEvaluationContext], "ScheduleEvaluationFunctionReturn"]
        if isinstance(self._execution_fn, DecoratedScheduleFunction):
            execution_fn = self._execution_fn.wrapped_fn
        else:
            execution_fn = cast(
                Callable[[ScheduleEvaluationContext], "ScheduleEvaluationFunctionReturn"],
                self._execution_fn,
            )

        result = list(ensure_gen(execution_fn(context)))

        skip_message: Optional[str] = None

        run_requests: List[RunRequest] = []
        if not result or result == [None]:
            run_requests = []
            skip_message = "Schedule function returned an empty result"
        elif len(result) == 1:
            item = check.inst(result[0], (SkipReason, RunRequest))
            if isinstance(item, RunRequest):
                run_requests = [item]
                skip_message = None
            elif isinstance(item, SkipReason):
                run_requests = []
                skip_message = item.skip_message
        else:
            # NOTE: mypy is not correctly reading this cast-- not sure why
            # (pyright reads it fine). Hence the type-ignores below.
            result = cast(List[RunRequest], check.is_list(result, of_type=RunRequest))  # type: ignore
            check.invariant(
                not any(not request.run_key for request in result),  # type: ignore
                (
                    "Schedules that return multiple RunRequests must specify a run_key in each"
                    " RunRequest"
                ),
            )
            run_requests = result  # type: ignore
            skip_message = None

        # clone all the run requests with the required schedule tags
        run_requests_with_schedule_tags = [
            request.with_replaced_attrs(
                tags=merge_dicts(request.tags, DagsterRun.tags_for_schedule(self))
            )
            for request in run_requests
        ]

        return ScheduleExecutionData(
            run_requests=run_requests_with_schedule_tags,
            skip_message=skip_message,
            captured_log_key=context.log_key if context.has_captured_logs() else None,
        )

    def has_loadable_target(self):
        return isinstance(self._target, DirectTarget)

    @property
    def targets_unresolved_asset_job(self) -> bool:
        return self.has_loadable_target() and isinstance(
            self.load_target(), UnresolvedAssetJobDefinition
        )

    def load_target(
        self,
    ) -> Union[GraphDefinition, PipelineDefinition, UnresolvedAssetJobDefinition]:
        if isinstance(self._target, DirectTarget):
            return self._target.load()

        check.failed("Target is not loadable")

    @public  # type: ignore
    @property
    def default_status(self) -> DefaultScheduleStatus:
        return self._default_status
