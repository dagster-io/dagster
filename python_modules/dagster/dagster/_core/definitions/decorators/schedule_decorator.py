import copy
from collections.abc import Mapping, Sequence
from functools import update_wrapper
from typing import TYPE_CHECKING, Callable, Optional, Union, cast

import dagster._check as check
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.resource_annotation import get_resource_args
from dagster._core.definitions.run_request import RunRequest, SkipReason
from dagster._core.definitions.schedule_definition import (
    DecoratedScheduleFunction,
    DefaultScheduleStatus,
    RawScheduleEvaluationFunction,
    RunRequestIterator,
    ScheduleDefinition,
    ScheduleEvaluationContext,
    has_at_least_one_parameter,
    validate_and_get_schedule_resource_dict,
)
from dagster._core.definitions.sensor_definition import get_context_param_name
from dagster._core.definitions.target import ExecutableDefinition
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    ScheduleExecutionError,
    user_code_error_boundary,
)
from dagster._utils import ensure_gen
from dagster._utils.tags import normalize_tags

if TYPE_CHECKING:
    from dagster._core.definitions.asset_selection import CoercibleToAssetSelection
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.unresolved_asset_job_definition import (
        UnresolvedAssetJobDefinition,
    )


def schedule(
    cron_schedule: Union[str, Sequence[str]],
    *,
    job_name: Optional[str] = None,
    name: Optional[str] = None,
    tags: Optional[Mapping[str, str]] = None,
    tags_fn: Optional[Callable[[ScheduleEvaluationContext], Optional[Mapping[str, str]]]] = None,
    metadata: Optional[RawMetadataMapping] = None,
    should_execute: Optional[Callable[[ScheduleEvaluationContext], bool]] = None,
    environment_vars: Optional[Mapping[str, str]] = None,
    execution_timezone: Optional[str] = None,
    description: Optional[str] = None,
    job: Optional[ExecutableDefinition] = None,
    default_status: DefaultScheduleStatus = DefaultScheduleStatus.STOPPED,
    required_resource_keys: Optional[set[str]] = None,
    target: Optional[
        Union[
            "CoercibleToAssetSelection",
            "AssetsDefinition",
            "JobDefinition",
            "UnresolvedAssetJobDefinition",
        ]
    ] = None,
) -> Callable[[RawScheduleEvaluationFunction], ScheduleDefinition]:
    """Creates a schedule following the provided cron schedule and requests runs for the provided job.

    The decorated function takes in a :py:class:`~dagster.ScheduleEvaluationContext` as its only
    argument, and does one of the following:

    1. Return a :py:class:`~dagster.RunRequest` object.
    2. Return a list of :py:class:`~dagster.RunRequest` objects.
    3. Return a :py:class:`~dagster.SkipReason` object, providing a descriptive message of why no runs were requested.
    4. Return nothing (skipping without providing a reason)
    5. Return a run config dictionary.
    6. Yield a :py:class:`~dagster.SkipReason` or yield one ore more :py:class:`~dagster.RunRequest` objects.

    Returns a :py:class:`~dagster.ScheduleDefinition`.

    Args:
        cron_schedule (Union[str, Sequence[str]]): A valid cron string or sequence of cron strings
            specifying when the schedule will run, e.g., ``45 23 * * 6`` for a schedule that runs
            at 11:45 PM every Saturday. If a sequence is provided, then the schedule will run for
            the union of all execution times for the provided cron strings, e.g.,
            ``['45 23 * * 6', '30 9 * * 0']`` for a schedule that runs at 11:45 PM every Saturday and
            9:30 AM every Sunday.
        name (Optional[str]): The name of the schedule.
        tags (Optional[Mapping[str, str]]): A set of key-value tags that annotate the schedule and can
            be used for searching and filtering in the UI.
        tags_fn (Optional[Callable[[ScheduleEvaluationContext], Optional[Dict[str, str]]]]): A function
            that generates tags to attach to the schedule's runs. Takes a
            :py:class:`~dagster.ScheduleEvaluationContext` and returns a dictionary of tags (string
            key-value pairs). **Note**: Either ``tags`` or ``tags_fn`` may be set, but not both.
        metadata (Optional[Mapping[str, Any]]): A set of metadata entries that annotate the
            schedule. Values will be normalized to typed `MetadataValue` objects.
        should_execute (Optional[Callable[[ScheduleEvaluationContext], bool]]): A function that runs at
            schedule execution time to determine whether a schedule should execute or skip. Takes a
            :py:class:`~dagster.ScheduleEvaluationContext` and returns a boolean (``True`` if the
            schedule should execute). Defaults to a function that always returns ``True``.
        execution_timezone (Optional[str]): Timezone in which the schedule should run.
            Supported strings for timezones are the ones provided by the
            `IANA time zone database <https://www.iana.org/time-zones>`_ - e.g. ``"America/Los_Angeles"``.
        description (Optional[str]): A human-readable description of the schedule.
        job (Optional[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]): The job
            that should execute when the schedule runs.
        default_status (DefaultScheduleStatus): If set to ``RUNNING``, the schedule will immediately be active when starting Dagster. The default status can be overridden from the Dagster UI or via the GraphQL API.
        required_resource_keys (Optional[Set[str]]): The set of resource keys required by the schedule.
        target (Optional[Union[CoercibleToAssetSelection, AssetsDefinition, JobDefinition, UnresolvedAssetJobDefinition]]):
            The target that the schedule will execute.
            It can take :py:class:`~dagster.AssetSelection` objects and anything coercible to it (e.g. `str`, `Sequence[str]`, `AssetKey`, `AssetsDefinition`).
            It can also accept :py:class:`~dagster.JobDefinition` (a function decorated with `@job` is an instance of `JobDefinition`) and `UnresolvedAssetJobDefinition` (the return value of :py:func:`~dagster.define_asset_job`) objects.
            This parameter will replace `job` and `job_name`.
    """

    def inner(fn: RawScheduleEvaluationFunction) -> ScheduleDefinition:
        from dagster._config.pythonic_config import validate_resource_annotated_function

        check.callable_param(fn, "fn")
        validate_resource_annotated_function(fn)

        schedule_name = name or fn.__name__

        validated_tags = None

        # perform upfront validation of schedule tags
        if tags_fn and tags:
            raise DagsterInvalidDefinitionError(
                "Attempted to provide both tags_fn and tags as arguments"
                " to ScheduleDefinition. Must provide only one of the two."
            )
        elif tags:
            validated_tags = normalize_tags(
                tags, allow_private_system_tags=False, warning_stacklevel=3
            )

        context_param_name = get_context_param_name(fn)
        resource_arg_names: set[str] = {arg.name for arg in get_resource_args(fn)}

        def _wrapped_fn(context: ScheduleEvaluationContext) -> RunRequestIterator:
            if should_execute:
                with user_code_error_boundary(
                    ScheduleExecutionError,
                    lambda: (
                        "Error occurred during the execution of should_execute for schedule"
                        f" {schedule_name}"
                    ),
                ):
                    if not should_execute(context):
                        yield SkipReason(
                            f"should_execute function for {schedule_name} returned false."
                        )
                        return
            resources = validate_and_get_schedule_resource_dict(
                context.resources, schedule_name, resource_arg_names
            )

            with user_code_error_boundary(
                ScheduleExecutionError,
                lambda: f"Error occurred during the evaluation of schedule {schedule_name}",
            ):
                context_param = {context_param_name: context} if context_param_name else {}
                result = fn(**context_param, **resources)

                if isinstance(result, dict):
                    # this is the run-config based decorated function, wrap the evaluated run config
                    # and tags in a RunRequest
                    evaluated_run_config = copy.deepcopy(result)
                    evaluated_tags = (
                        validated_tags
                        or (
                            tags_fn
                            and normalize_tags(tags_fn(context), allow_private_system_tags=False)
                        )
                        or None
                    )
                    yield RunRequest(
                        run_key=None,
                        run_config=evaluated_run_config,
                        tags=evaluated_tags,
                    )
                elif isinstance(result, list):
                    yield from cast(list[RunRequest], result)
                else:
                    # this is a run-request based decorated function
                    yield from cast(RunRequestIterator, ensure_gen(result))

        has_context_arg = has_at_least_one_parameter(fn)
        evaluation_fn = DecoratedScheduleFunction(
            decorated_fn=fn,
            wrapped_fn=_wrapped_fn,
            has_context_arg=has_context_arg,
        )

        schedule_def = ScheduleDefinition.dagster_internal_init(
            name=schedule_name,
            cron_schedule=cron_schedule,
            job_name=job_name,
            environment_vars=environment_vars,
            execution_timezone=execution_timezone,
            description=description,
            execution_fn=evaluation_fn,
            job=job,
            default_status=default_status,
            required_resource_keys=required_resource_keys,
            run_config=None,  # cannot supply run_config or run_config_fn to decorator
            run_config_fn=None,
            tags=tags,
            tags_fn=None,  # cannot supply tags or tags_fn to decorator
            metadata=metadata,
            should_execute=None,  # already encompassed in evaluation_fn
            target=target,
        )

        update_wrapper(schedule_def, wrapped=fn)

        return schedule_def

    return inner
