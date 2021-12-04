import copy
from contextlib import ExitStack
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, NamedTuple, Optional, Union, cast

import pendulum
from croniter import croniter
from dagster import check
from dagster.seven import funcsigs

from ...serdes import whitelist_for_serdes
from ...utils import ensure_gen, merge_dicts
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
from ..storage.pipeline_run import PipelineRun
from ..storage.tags import check_tags
from .graph_definition import GraphDefinition
from .mode import DEFAULT_MODE_NAME
from .pipeline_definition import PipelineDefinition
from .run_request import JobType, RunRequest, SkipReason
from .target import DirectTarget, RepoRelativeTarget
from .utils import check_valid_name

if TYPE_CHECKING:
    from .decorators.schedule import DecoratedScheduleFunction


class ScheduleEvaluationContext:
    """Schedule-specific execution context.

    An instance of this class is made available as the first argument to various ScheduleDefinition
    functions. It is passed as the first argument to ``run_config_fn``, ``tags_fn``,
    and ``should_execute``.

    Attributes:
        instance_ref (Optional[InstanceRef]): The serialized instance configured to run the schedule
        scheduled_execution_time (datetime):
            The time in which the execution was scheduled to happen. May differ slightly
            from both the actual execution time and the time at which the run config is computed.
            Not available in all schedulers - currently only set in deployments using
            DagsterDaemonScheduler.
    """

    __slots__ = ["_instance_ref", "_scheduled_execution_time", "_exit_stack", "_instance"]

    def __init__(
        self, instance_ref: Optional[InstanceRef], scheduled_execution_time: Optional[datetime]
    ):
        self._exit_stack = ExitStack()
        self._instance = None

        self._instance_ref = check.opt_inst_param(instance_ref, "instance_ref", InstanceRef)
        self._scheduled_execution_time = check.opt_inst_param(
            scheduled_execution_time, "scheduled_execution_time", datetime
        )

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()

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

    @property
    def scheduled_execution_time(self) -> Optional[datetime]:
        return self._scheduled_execution_time


# Preserve ScheduleExecutionContext for backcompat so type annotations don't break.
ScheduleExecutionContext = ScheduleEvaluationContext


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
class ScheduleExecutionData(NamedTuple):
    run_requests: Optional[List[RunRequest]]
    skip_message: Optional[str]


class ScheduleDefinition:
    """Define a schedule that targets a job

    Args:
        name (Optional[str]): The name of the schedule to create. Defaults to the job name plus
            "_schedule".
        cron_schedule (str): A valid cron string specifying when the schedule will run, e.g.,
            '45 23 * * 6' for a schedule that runs at 11:45 PM every Saturday.
        pipeline_name (Optional[str]): (legacy) The name of the pipeline to execute when the schedule runs.
        execution_fn (Callable[ScheduleEvaluationContext]): The core evaluation function for the
            schedule, which is run at an interval to determine whether a run should be launched or
            not. Takes a :py:class:`~dagster.ScheduleEvaluationContext`.

            This function must return a generator, which must yield either a single SkipReason
            or one or more RunRequest objects.
        run_config (Optional[Dict]): The config that parameterizes this execution,
            as a dict.
        run_config_fn (Optional[Callable[[ScheduleEvaluationContext], [Dict]]]): A function that
            takes a ScheduleEvaluationContext object and returns the run configuration that
            parameterizes this execution, as a dict. You may set only one of ``run_config``,
            ``run_config_fn``, and ``execution_fn``.
        tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the scheduled runs.
        tags_fn (Optional[Callable[[ScheduleEvaluationContext], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the schedules runs. Takes a
            :py:class:`~dagster.ScheduleEvaluationContext` and returns a dictionary of tags (string
            key-value pairs). You may set only one of ``tags``, ``tags_fn``, and ``execution_fn``.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the schedule runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): (legacy) The mode to apply when executing this schedule. (default: 'default')
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
    """

    def __init__(
        self,
        name: Optional[str] = None,
        cron_schedule: Optional[str] = None,
        pipeline_name: Optional[str] = None,
        run_config: Optional[Any] = None,
        run_config_fn: Optional[Callable[..., Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        tags_fn: Optional[Callable[..., Optional[Dict[str, str]]]] = None,
        solid_selection: Optional[List[Any]] = None,
        mode: Optional[str] = "default",
        should_execute: Optional[Callable[..., bool]] = None,
        environment_vars: Optional[Dict[str, str]] = None,
        execution_timezone: Optional[str] = None,
        execution_fn: Optional[
            Union[Callable[[ScheduleEvaluationContext], Any], "DecoratedScheduleFunction"]
        ] = None,
        description: Optional[str] = None,
        job: Optional[Union[GraphDefinition, PipelineDefinition]] = None,
    ):
        from .decorators.schedule import DecoratedScheduleFunction

        self._cron_schedule = check.str_param(cron_schedule, "cron_schedule")

        if not croniter.is_valid(self._cron_schedule):
            raise DagsterInvalidDefinitionError(
                f"Found invalid cron schedule '{self._cron_schedule}' for schedule '{name}''."
            )

        if job is not None:
            self._target: Union[DirectTarget, RepoRelativeTarget] = DirectTarget(job)
        else:
            self._target = RepoRelativeTarget(
                pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
                mode=check.opt_str_param(mode, "mode") or DEFAULT_MODE_NAME,
                solid_selection=check.opt_nullable_list_param(
                    solid_selection, "solid_selection", of_type=str
                ),
            )

        if name:
            self._name = check_valid_name(name)
        elif pipeline_name:
            self._name = pipeline_name + "_schedule"
        elif job:
            self._name = job.name + "_schedule"

        self._description = check.opt_str_param(description, "description")

        self._environment_vars = check.opt_dict_param(
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
            self._run_config_fn = check.opt_callable_param(
                run_config_fn,
                "run_config_fn",
                default=lambda _context: check.opt_dict_param(run_config, "run_config"),
            )

            if tags_fn and tags:
                raise DagsterInvalidDefinitionError(
                    "Attempted to provide both tags_fn and tags as arguments"
                    " to ScheduleDefinition. Must provide only one of the two."
                )
            elif tags:
                check_tags(tags, "tags")
                tags_fn = lambda _context: tags
            else:
                tags_fn = check.opt_callable_param(tags_fn, "tags_fn", default=lambda _context: {})

            should_execute = check.opt_callable_param(
                should_execute, "should_execute", default=lambda _context: True
            )

            def _execution_fn(context):
                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of should_execute for schedule {name}",
                ):
                    if not should_execute(context):
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
                    evaluated_run_config = copy.deepcopy(
                        self._run_config_fn(context)
                        if is_context_provided(get_function_params(self._run_config_fn))
                        else self._run_config_fn()
                    )

                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: f"Error occurred during the execution of tags_fn for schedule {name}",
                ):
                    evaluated_tags = tags_fn(context)

                yield RunRequest(
                    run_key=None,
                    run_config=evaluated_run_config,
                    tags=evaluated_tags,
                )

            self._execution_fn = _execution_fn

        if self._execution_timezone:
            try:
                # Verify that the timezone can be loaded
                pendulum.timezone(self._execution_timezone)
            except Exception:
                raise DagsterInvalidDefinitionError(
                    "Invalid execution timezone {timezone} for {schedule_name}".format(
                        schedule_name=name, timezone=self._execution_timezone
                    )
                )

    def __call__(self, *args, **kwargs):
        from .decorators.schedule import DecoratedScheduleFunction

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

            result = self._execution_fn.decorated_fn(context)
        else:
            if len(args) + len(kwargs) > 0:
                raise DagsterInvalidInvocationError(
                    "Decorated schedule function takes no arguments, but arguments were provided."
                )
            result = self._execution_fn.decorated_fn()

        if isinstance(result, dict):
            return copy.deepcopy(result)
        else:
            return result

    @property
    def name(self) -> str:
        return self._name

    @property
    def pipeline_name(self) -> str:
        return self._target.pipeline_name

    @property
    def job_type(self) -> JobType:
        return JobType.SCHEDULE

    @property
    def solid_selection(self) -> Optional[List[Any]]:
        return self._target.solid_selection

    @property
    def mode(self) -> str:
        return self._target.mode

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def cron_schedule(self) -> str:
        return self._cron_schedule

    @property
    def environment_vars(self) -> Dict[str, str]:
        return self._environment_vars

    @property
    def execution_timezone(self) -> Optional[str]:
        return self._execution_timezone

    def evaluate_tick(self, context: "ScheduleEvaluationContext") -> ScheduleExecutionData:
        """Evaluate schedule using the provided context.

        Args:
            context (ScheduleEvaluationContext): The context with which to evaluate this schedule.
        Returns:
            ScheduleExecutionData: Contains list of run requests, or skip message if present.

        """

        from .decorators.schedule import DecoratedScheduleFunction

        check.inst_param(context, "context", ScheduleEvaluationContext)
        if isinstance(self._execution_fn, DecoratedScheduleFunction):
            execution_fn = self._execution_fn.wrapped_fn
        else:
            execution_fn = cast(Callable[[ScheduleEvaluationContext], Any], self._execution_fn)
        result = list(ensure_gen(execution_fn(context)))

        if not result or result == [None]:
            run_requests = []
            skip_message = None
        elif len(result) == 1:
            item = result[0]
            check.inst(item, (SkipReason, RunRequest))
            run_requests = [item] if isinstance(item, RunRequest) else []
            skip_message = item.skip_message if isinstance(item, SkipReason) else None
        else:
            check.is_list(result, of_type=RunRequest)
            check.invariant(
                not any(not request.run_key for request in result),
                "Schedules that return multiple RunRequests must specify a run_key in each RunRequest",
            )
            run_requests = result
            skip_message = None

        # clone all the run requests with the required schedule tags
        run_requests_with_schedule_tags = [
            RunRequest(
                run_key=request.run_key,
                run_config=request.run_config,
                tags=merge_dicts(request.tags, PipelineRun.tags_for_schedule(self)),
            )
            for request in run_requests
        ]

        return ScheduleExecutionData(
            run_requests=run_requests_with_schedule_tags, skip_message=skip_message
        )

    def has_loadable_target(self):
        return isinstance(self._target, DirectTarget)

    def load_target(self):
        if isinstance(self._target, DirectTarget):
            return self._target.load()

        check.failed("Target is not loadable")


def is_context_provided(params: List[funcsigs.Parameter]) -> bool:
    return len(params) == 1
