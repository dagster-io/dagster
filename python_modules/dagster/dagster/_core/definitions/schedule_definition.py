import copy
import logging
from contextlib import ExitStack
from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    TypeVar,
    Union,
    cast,
)

import pendulum
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._core.definitions.instigation_logger import InstigationLogger
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.scoped_resources_builder import Resources, ScopedResourcesBuilder
from dagster._serdes import whitelist_for_serdes
from dagster._utils import IHasInternalInit, ensure_gen
from dagster._utils.backcompat import deprecation_warning
from dagster._utils.merger import merge_dicts
from dagster._utils.schedules import is_valid_cron_schedule

from ..decorator_utils import has_at_least_one_parameter
from ..errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from ..instance import DagsterInstance
from ..instance.ref import InstanceRef
from ..storage.dagster_run import DagsterRun
from .graph_definition import GraphDefinition
from .job_definition import JobDefinition
from .run_request import RunRequest, SkipReason
from .target import DirectTarget, ExecutableDefinition, RepoRelativeTarget
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from .utils import check_valid_name, validate_tags

if TYPE_CHECKING:
    from dagster import ResourceDefinition
    from dagster._core.definitions.repository_definition import RepositoryDefinition
T = TypeVar("T")

RunConfig: TypeAlias = Mapping[str, Any]
RunRequestIterator: TypeAlias = Iterator[Union[RunRequest, SkipReason]]

ScheduleEvaluationFunctionReturn: TypeAlias = Union[
    RunRequest, SkipReason, RunConfig, RunRequestIterator, Sequence[RunRequest]
]
RawScheduleEvaluationFunction: TypeAlias = Callable[..., ScheduleEvaluationFunctionReturn]

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


def get_or_create_schedule_context(
    fn: Callable, *args: Any, **kwargs: Any
) -> "ScheduleEvaluationContext":
    """Based on the passed resource function and the arguments passed to it, returns the
    user-passed ScheduleEvaluationContext or creates one if it is not passed.

    Raises an exception if the user passes more than one argument or if the user-provided
    function requires a context parameter but none is passed.
    """
    from dagster._config.pythonic_config import is_coercible_to_resource
    from dagster._core.definitions.sensor_definition import get_context_param_name

    context_param_name = get_context_param_name(fn)

    kwarg_keys_non_resource = set(kwargs.keys()) - {param.name for param in get_resource_args(fn)}
    if len(args) + len(kwarg_keys_non_resource) > 1:
        raise DagsterInvalidInvocationError(
            "Schedule invocation received multiple non-resource arguments. Only a first "
            "positional context parameter should be provided when invoking."
        )

    if any(is_coercible_to_resource(arg) for arg in args):
        raise DagsterInvalidInvocationError(
            "If directly invoking a schedule, you may not provide resources as"
            " positional arguments, only as keyword arguments."
        )

    context: Optional[ScheduleEvaluationContext] = None

    if len(args) > 0:
        context = check.opt_inst(args[0], ScheduleEvaluationContext)
    elif len(kwargs) > 0:
        if context_param_name and context_param_name not in kwargs:
            raise DagsterInvalidInvocationError(
                f"Schedule invocation expected argument '{context_param_name}'."
            )
        context = check.opt_inst(
            kwargs.get(context_param_name or "context"), ScheduleEvaluationContext
        )
    elif context_param_name:
        # If the context parameter is present but no value was provided, we error
        raise DagsterInvalidInvocationError(
            "Schedule evaluation function expected context argument, but no context argument "
            "was provided when invoking."
        )

    context = context or build_schedule_context()
    resource_args_from_kwargs = {}

    resource_args = {param.name for param in get_resource_args(fn)}
    for resource_arg in resource_args:
        if resource_arg in kwargs:
            resource_args_from_kwargs[resource_arg] = kwargs[resource_arg]

    if resource_args_from_kwargs:
        return context.merge_resources(resource_args_from_kwargs)

    return context


class ScheduleEvaluationContext:
    """The context object available as the first argument various functions defined on a :py:class:`dagster.ScheduleDefinition`.

    A `ScheduleEvaluationContext` object is passed as the first argument to ``run_config_fn``, ``tags_fn``,
    and ``should_execute``.

    Users should not instantiate this object directly. To construct a `ScheduleEvaluationContext` for testing purposes, use :py:func:`dagster.build_schedule_context`.

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
        "_resource_defs",
        "_schedule_name",
        "_resources_cm",
        "_resources",
        "_cm_scope_entered",
        "_repository_def",
    ]

    def __init__(
        self,
        instance_ref: Optional[InstanceRef],
        scheduled_execution_time: Optional[datetime],
        repository_name: Optional[str] = None,
        schedule_name: Optional[str] = None,
        resources: Optional[Mapping[str, "ResourceDefinition"]] = None,
        repository_def: Optional["RepositoryDefinition"] = None,
    ):
        from dagster._core.definitions.repository_definition import RepositoryDefinition

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

        # Wait to set resources unless they're accessed
        self._resource_defs = resources
        self._resources = None
        self._cm_scope_entered = False
        self._repository_def = check.opt_inst_param(
            repository_def, "repository_def", RepositoryDefinition
        )

    def __enter__(self) -> "ScheduleEvaluationContext":
        self._cm_scope_entered = True
        return self

    def __exit__(self, *exc) -> None:
        self._exit_stack.close()
        self._logger = None

    @property
    def resource_defs(self) -> Optional[Mapping[str, "ResourceDefinition"]]:
        return self._resource_defs

    @public
    @property
    def resources(self) -> Resources:
        """Mapping of resource key to resource definition to be made available
        during schedule execution.
        """
        from dagster._core.definitions.scoped_resources_builder import (
            IContainsGenerator,
        )
        from dagster._core.execution.build_resources import build_resources

        if not self._resources:
            # Early exit if no resources are defined. This skips unnecessary initialization
            # entirely. This allows users to run user code servers in cases where they
            # do not have access to the instance if they use a subset of features do
            # that do not require instance access. In this case, if they do not use
            # resources on schedules they do not require the instance, so we do not
            # instantiate it
            #
            # Tracking at https://github.com/dagster-io/dagster/issues/14345
            if not self._resource_defs:
                self._resources = ScopedResourcesBuilder.build_empty()
                return self._resources

            instance = self.instance if self._instance or self._instance_ref else None

            resources_cm = build_resources(resources=self._resource_defs, instance=instance)
            self._resources = self._exit_stack.enter_context(resources_cm)

            if isinstance(self._resources, IContainsGenerator) and not self._cm_scope_entered:
                self._exit_stack.close()
                raise DagsterInvariantViolationError(
                    "At least one provided resource is a generator, but attempting to access"
                    " resources outside of context manager scope. You can use the following syntax"
                    " to open a context manager: `with build_sensor_context(...) as context:`"
                )

        return self._resources

    def merge_resources(self, resources_dict: Mapping[str, Any]) -> "ScheduleEvaluationContext":
        """Merge the specified resources into this context.
        This method is intended to be used by the Dagster framework, and should not be called by user code.

        Args:
            resources_dict (Mapping[str, Any]): The resources to replace in the context.
        """
        check.invariant(
            self._resources is None, "Cannot merge resources in context that has been initialized."
        )
        from dagster._core.execution.build_resources import wrap_resources_for_execution

        return ScheduleEvaluationContext(
            instance_ref=self._instance_ref,
            scheduled_execution_time=self._scheduled_execution_time,
            repository_name=self._repository_name,
            schedule_name=self._schedule_name,
            resources={
                **(self._resource_defs or {}),
                **wrap_resources_for_execution(resources_dict),
            },
            repository_def=self._repository_def,
        )

    @public
    @property
    def instance(self) -> "DagsterInstance":
        """DagsterInstance: The current DagsterInstance."""
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

    @property
    def instance_ref(self) -> Optional[InstanceRef]:
        """The serialized instance configured to run the schedule."""
        return self._instance_ref

    @public
    @property
    def scheduled_execution_time(self) -> datetime:
        """The time in which the execution was scheduled to happen. May differ slightly
        from both the actual execution time and the time at which the run config is computed.
        """
        if self._scheduled_execution_time is None:
            check.failed(
                "Attempting to access scheduled_execution_time, but no scheduled_execution_time was"
                " set on this context"
            )

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

    @property
    def repository_def(self) -> "RepositoryDefinition":
        if not self._repository_def:
            raise DagsterInvariantViolationError(
                "Attempted to access repository_def, but no repository_def was provided."
            )
        return self._repository_def


class DecoratedScheduleFunction(NamedTuple):
    """Wrapper around the decorated schedule function.  Keeps track of both to better support the
    optimal return value for direct invocation of the evaluation function.
    """

    decorated_fn: RawScheduleEvaluationFunction
    wrapped_fn: Callable[[ScheduleEvaluationContext], RunRequestIterator]
    has_context_arg: bool


def build_schedule_context(
    instance: Optional[DagsterInstance] = None,
    scheduled_execution_time: Optional[datetime] = None,
    resources: Optional[Mapping[str, object]] = None,
    repository_def: Optional["RepositoryDefinition"] = None,
    instance_ref: Optional["InstanceRef"] = None,
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

    """
    from dagster._core.execution.build_resources import wrap_resources_for_execution

    check.opt_inst_param(instance, "instance", DagsterInstance)

    return ScheduleEvaluationContext(
        instance_ref=instance_ref
        if instance_ref
        else instance.get_ref()
        if instance and instance.is_persistent
        else None,
        scheduled_execution_time=check.opt_inst_param(
            scheduled_execution_time, "scheduled_execution_time", datetime
        ),
        resources=wrap_resources_for_execution(resources),
        repository_def=repository_def,
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


def validate_and_get_schedule_resource_dict(
    resources: Resources, schedule_name: str, required_resource_keys: Set[str]
) -> Dict[str, Any]:
    """Validates that the context has all the required resources and returns a dictionary of
    resource key to resource object.
    """
    for k in required_resource_keys:
        if not hasattr(resources, k):
            raise DagsterInvalidDefinitionError(
                f"Resource with key '{k}' required by schedule '{schedule_name}' was not provided."
            )

    return {k: getattr(resources, k) for k in required_resource_keys}


class ScheduleDefinition(IHasInternalInit):
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
        execution_timezone (Optional[str]): Timezone in which the schedule should run.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>` - e.g. "America/Los_Angeles".
        description (Optional[str]): A human-readable description of the schedule.
        job (Optional[Union[GraphDefinition, JobDefinition]]): The job that should execute when this
            schedule runs.
        default_status (DefaultScheduleStatus): Whether the schedule starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        required_resource_keys (Optional[Set[str]]): The set of resource keys required by the schedule.
    """

    def with_updated_job(self, new_job: ExecutableDefinition) -> "ScheduleDefinition":
        """Returns a copy of this schedule with the job replaced.

        Args:
            job (ExecutableDefinition): The job that should execute when this
                schedule runs.
        """
        return ScheduleDefinition.dagster_internal_init(
            name=self.name,
            cron_schedule=self._cron_schedule,
            job_name=self.job_name,
            execution_timezone=self.execution_timezone,
            execution_fn=self._execution_fn,
            description=self.description,
            job=new_job,
            default_status=self.default_status,
            environment_vars=self._environment_vars,
            required_resource_keys=self.required_resource_keys,
            run_config=None,  # run_config, tags, should_execute encapsulated in execution_fn
            run_config_fn=None,
            tags=None,
            tags_fn=None,
            should_execute=None,
        )

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
        required_resource_keys: Optional[Set[str]] = None,
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
                job_name=check.str_param(job_name, "job_name"),
                op_selection=None,
            )

        if name:
            self._name = check_valid_name(name)
        elif job_name:
            self._name = job_name + "_schedule"
        elif job:
            self._name = job.name + "_schedule"

        self._description = check.opt_str_param(description, "description")

        if environment_vars is not None:
            deprecation_warning(
                "`environment_vars` parameter to `ScheduleDefinition`",
                "2.0.0",
                (
                    "It is no longer necessary. Schedules will have access to all environment"
                    " variables set in the containing environment, and can safely be deleted."
                ),
            )
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
                tags_fn = lambda _context: tags
            else:
                tags_fn = check.opt_callable_param(
                    tags_fn, "tags_fn", default=lambda _context: cast(Mapping[str, str], {})
                )
            self._tags_fn = tags_fn
            self._tags = tags

            self._should_execute: ScheduleShouldExecuteFunction = check.opt_callable_param(
                should_execute, "should_execute", default=lambda _context: True
            )

            # Several type-ignores are present in this function to work around bugs in mypy
            # inference.
            def _execution_fn(context: ScheduleEvaluationContext) -> RunRequestIterator:
                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of should_execute for schedule {name}",
                ):
                    if not self._should_execute(context):
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
                        if has_at_least_one_parameter(_run_config_fn)
                        else _run_config_fn()  # type: ignore  # (strict type guard)
                    )

                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of tags_fn for schedule {name}",
                ):
                    evaluated_tags = validate_tags(tags_fn(context), allow_reserved_tags=False)

                yield RunRequest(
                    run_key=None,
                    run_config=evaluated_run_config,
                    tags=evaluated_tags,
                )

            self._execution_fn = _execution_fn

        if self._execution_timezone:
            try:
                # Verify that the timezone can be loaded
                pendulum.tz.timezone(self._execution_timezone)  # type: ignore
            except Exception as e:
                raise DagsterInvalidDefinitionError(
                    f"Invalid execution timezone {self._execution_timezone} for {name}"
                ) from e

        self._default_status = check.inst_param(
            default_status, "default_status", DefaultScheduleStatus
        )

        resource_arg_names: Set[str] = (
            {arg.name for arg in get_resource_args(self._execution_fn.decorated_fn)}
            if isinstance(self._execution_fn, DecoratedScheduleFunction)
            else set()
        )

        check.param_invariant(
            len(required_resource_keys or []) == 0 or len(resource_arg_names) == 0,
            (
                "Cannot specify resource requirements in both @sensor decorator and as arguments to"
                " the decorated function"
            ),
        )

        self._required_resource_keys = (
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
            or resource_arg_names
        )

    @staticmethod
    def dagster_internal_init(
        *,
        name: Optional[str],
        cron_schedule: Optional[Union[str, Sequence[str]]],
        job_name: Optional[str],
        run_config: Optional[Any],
        run_config_fn: Optional[ScheduleRunConfigFunction],
        tags: Optional[Mapping[str, str]],
        tags_fn: Optional[ScheduleTagsFunction],
        should_execute: Optional[ScheduleShouldExecuteFunction],
        environment_vars: Optional[Mapping[str, str]],
        execution_timezone: Optional[str],
        execution_fn: Optional[ScheduleExecutionFunction],
        description: Optional[str],
        job: Optional[ExecutableDefinition],
        default_status: DefaultScheduleStatus,
        required_resource_keys: Optional[Set[str]],
    ) -> "ScheduleDefinition":
        return ScheduleDefinition(
            name=name,
            cron_schedule=cron_schedule,
            job_name=job_name,
            run_config=run_config,
            run_config_fn=run_config_fn,
            tags=tags,
            tags_fn=tags_fn,
            should_execute=should_execute,
            environment_vars=environment_vars,
            execution_timezone=execution_timezone,
            execution_fn=execution_fn,
            description=description,
            job=job,
            default_status=default_status,
            required_resource_keys=required_resource_keys,
        )

    def __call__(self, *args, **kwargs) -> ScheduleEvaluationFunctionReturn:
        from dagster._core.definitions.sensor_definition import get_context_param_name

        from .decorators.schedule_decorator import DecoratedScheduleFunction

        if not isinstance(self._execution_fn, DecoratedScheduleFunction):
            raise DagsterInvalidInvocationError(
                "Schedule invocation is only supported for schedules created via the schedule "
                "decorators."
            )

        context_param_name = get_context_param_name(self._execution_fn.decorated_fn)
        context = get_or_create_schedule_context(self._execution_fn.decorated_fn, *args, **kwargs)
        context_param = {context_param_name: context} if context_param_name else {}

        resources = validate_and_get_schedule_resource_dict(
            context.resources, self._name, self._required_resource_keys
        )
        result = self._execution_fn.decorated_fn(**context_param, **resources)

        if isinstance(result, dict):
            return copy.deepcopy(result)
        else:
            return result

    @public
    @property
    def name(self) -> str:
        """str: The name of the schedule."""
        return self._name

    @public
    @property
    def job_name(self) -> str:
        """str: The name of the job targeted by this schedule."""
        return self._target.job_name

    @public
    @property
    def description(self) -> Optional[str]:
        """Optional[str]: A description for this schedule."""
        return self._description

    @public
    @property
    def cron_schedule(self) -> Union[str, Sequence[str]]:
        """Union[str, Sequence[str]]: The cron schedule representing when this schedule will be evaluated.
        """
        return self._cron_schedule  # type: ignore

    @deprecated
    @property
    def environment_vars(self) -> Mapping[str, str]:
        return self._environment_vars

    @public
    @property
    def required_resource_keys(self) -> Set[str]:
        """Set[str]: The set of keys for resources that must be provided to this schedule."""
        return self._required_resource_keys

    @public
    @property
    def execution_timezone(self) -> Optional[str]:
        """Optional[str]: The timezone in which this schedule will be evaluated."""
        return self._execution_timezone

    @public
    @property
    def job(self) -> Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]:
        """Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]: The job that is
        targeted by this schedule.
        """
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
        from dagster._core.definitions.partition import CachingDynamicPartitionsLoader

        check.inst_param(context, "context", ScheduleEvaluationContext)
        execution_fn: Callable[..., "ScheduleEvaluationFunctionReturn"]
        if isinstance(self._execution_fn, DecoratedScheduleFunction):
            execution_fn = self._execution_fn.wrapped_fn
        else:
            execution_fn = cast(
                Callable[..., "ScheduleEvaluationFunctionReturn"],
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
            result = cast(List[RunRequest], check.is_list(result, of_type=RunRequest))
            check.invariant(
                not any(not request.run_key for request in result),
                (
                    "Schedules that return multiple RunRequests must specify a run_key in each"
                    " RunRequest"
                ),
            )
            run_requests = result
            skip_message = None

        dynamic_partitions_store = (
            CachingDynamicPartitionsLoader(context.instance) if context.instance_ref else None
        )

        # clone all the run requests with resolved tags and config
        resolved_run_requests = []
        for run_request in run_requests:
            if run_request.partition_key and not run_request.has_resolved_partition():
                if context.repository_def is None:
                    raise DagsterInvariantViolationError(
                        "Must provide repository def to build_schedule_context when yielding"
                        " partitioned run requests"
                    )

                scheduled_target = context.repository_def.get_job(self._target.job_name)
                resolved_request = run_request.with_resolved_tags_and_config(
                    target_definition=scheduled_target,
                    dynamic_partitions_requests=[],
                    current_time=context.scheduled_execution_time,
                    dynamic_partitions_store=dynamic_partitions_store,
                )
            else:
                resolved_request = run_request

            resolved_run_requests.append(
                resolved_request.with_replaced_attrs(
                    tags=merge_dicts(resolved_request.tags, DagsterRun.tags_for_schedule(self))
                )
            )

        return ScheduleExecutionData(
            run_requests=resolved_run_requests,
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
    ) -> Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]:
        if isinstance(self._target, DirectTarget):
            return self._target.load()

        check.failed("Target is not loadable")

    @public
    @property
    def default_status(self) -> DefaultScheduleStatus:
        """DefaultScheduleStatus: The default status for this schedule when it is first loaded in
        a code location.
        """
        return self._default_status
