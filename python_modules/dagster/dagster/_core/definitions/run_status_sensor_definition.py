import warnings
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, Sequence, Union, cast

import pendulum

import dagster._check as check
from dagster._annotations import PublicAttr
from dagster._core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    RunStatusSensorExecutionError,
    user_code_error_boundary,
)
from dagster._core.events import PIPELINE_RUN_STATUS_TO_EVENT_TYPE, DagsterEvent
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRun, DagsterRunStatus, PipelineRun, RunsFilter
from dagster._serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster._serdes.errors import DeserializationError
from dagster._serdes.serdes import register_serdes_tuple_fallbacks
from dagster._seven import JSONDecodeError
from dagster._utils import utc_datetime_from_timestamp
from dagster._utils.backcompat import deprecation_warning
from dagster._utils.error import serializable_error_info_from_exc_info

from ..decorator_utils import get_function_params
from .graph_definition import GraphDefinition
from .job_definition import JobDefinition
from .pipeline_definition import PipelineDefinition
from .sensor_definition import (
    DefaultSensorStatus,
    PipelineRunReaction,
    RawSensorEvaluationFunctionReturn,
    RunRequest,
    SensorDefinition,
    SensorEvaluationContext,
    SkipReason,
    is_context_provided,
)
from .unresolved_asset_job_definition import UnresolvedAssetJobDefinition

if TYPE_CHECKING:
    from dagster._core.host_representation.selector import JobSelector, RepositorySelector


@whitelist_for_serdes
class RunStatusSensorCursor(
    NamedTuple(
        "_RunStatusSensorCursor",
        [("record_id", int), ("update_timestamp", str)],
    )
):
    def __new__(cls, record_id, update_timestamp):

        return super(RunStatusSensorCursor, cls).__new__(
            cls,
            record_id=check.int_param(record_id, "record_id"),
            update_timestamp=check.str_param(update_timestamp, "update_timestamp"),
        )

    @staticmethod
    def is_valid(json_str: str) -> bool:
        try:
            obj = deserialize_json_to_dagster_namedtuple(json_str)
            return isinstance(obj, RunStatusSensorCursor)
        except (JSONDecodeError, DeserializationError):
            return False

    def to_json(self) -> str:
        return serialize_dagster_namedtuple(cast(NamedTuple, self))

    @staticmethod
    def from_json(json_str: str) -> tuple:
        return deserialize_json_to_dagster_namedtuple(json_str)


# handle backcompat
register_serdes_tuple_fallbacks({"PipelineSensorCursor": RunStatusSensorCursor})


class RunStatusSensorContext(
    NamedTuple(
        "_RunStatusSensorContext",
        [
            ("sensor_name", PublicAttr[str]),
            ("dagster_run", PublicAttr[DagsterRun]),
            ("dagster_event", PublicAttr[DagsterEvent]),
            ("instance", PublicAttr[DagsterInstance]),
        ],
    )
):
    """The ``context`` object available to a decorated function of ``run_status_sensor``.

    Attributes:
        sensor_name (str): the name of the sensor.
        dagster_run (DagsterRun): the run of the job or pipeline.
        dagster_event (DagsterEvent): the event associated with the job or pipeline run status.
        instance (DagsterInstance): the current instance.
    """

    def __new__(cls, sensor_name, dagster_run, dagster_event, instance):

        return super(RunStatusSensorContext, cls).__new__(
            cls,
            sensor_name=check.str_param(sensor_name, "sensor_name"),
            dagster_run=check.inst_param(dagster_run, "dagster_run", DagsterRun),
            dagster_event=check.inst_param(dagster_event, "dagster_event", DagsterEvent),
            instance=check.inst_param(instance, "instance", DagsterInstance),
        )

    def for_run_failure(self):
        """Converts RunStatusSensorContext to RunFailureSensorContext."""
        return RunFailureSensorContext(
            sensor_name=self.sensor_name,
            dagster_run=self.dagster_run,
            dagster_event=self.dagster_event,
            instance=self.instance,
        )

    @property
    def pipeline_run(self) -> PipelineRun:
        warnings.warn(
            "`RunStatusSensorContext.pipeline_run` is deprecated as of 0.13.0; use "
            "`RunStatusSensorContext.dagster_run` instead."
        )
        return self.dagster_run


class RunFailureSensorContext(RunStatusSensorContext):
    """The ``context`` object available to a decorated function of ``run_failure_sensor``.

    Attributes:
        sensor_name (str): the name of the sensor.
        dagster_run (DagsterRun): the failed pipeline run.
        failure_event (DagsterEvent): the pipeline failure event.
    """

    @property
    def failure_event(self):
        return self.dagster_event


def build_run_status_sensor_context(
    sensor_name: str,
    dagster_event: DagsterEvent,
    dagster_instance: DagsterInstance,
    dagster_run: DagsterRun,
) -> RunStatusSensorContext:
    """
    Builds run status sensor context from provided parameters.

    This function can be used to provide the context argument when directly invoking a function
    decorated with `@run_status_sensor` or `@run_failure_sensor`, such as when writing unit tests.

    Args:
        sensor_name (str): The name of the sensor the context is being constructed for.
        dagster_event (DagsterEvent): A DagsterEvent with the same event type as the one that
            triggers the run_status_sensor
        dagster_instance (DagsterInstance): The dagster instance configured for the context.
        dagster_run (DagsterRun): DagsterRun object from running a job

    Examples:
        .. code-block:: python

            instance = DagsterInstance.ephemeral()
            result = my_job.execute_in_process(instance=instance)

            dagster_run = result.dagster_run
            dagster_event = result.get_job_success_event() # or get_job_failure_event()

            context = build_run_status_sensor_context(
                sensor_name="run_status_sensor_to_invoke",
                dagster_instance=instance,
                dagster_run=dagster_run,
                dagster_event=dagster_event,
            )
            run_status_sensor_to_invoke(context)
    """

    return RunStatusSensorContext(
        sensor_name=sensor_name,
        instance=dagster_instance,
        dagster_run=dagster_run,
        dagster_event=dagster_event,
    )


def run_failure_sensor(
    name: Optional[Union[Callable[..., Any], str]] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    monitored_jobs: Optional[
        Sequence[
            Union[
                PipelineDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
            ]
        ]
    ] = None,
    job_selection: Optional[
        Sequence[
            Union[
                PipelineDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
            ]
        ]
    ] = None,
    monitor_all_repositories: bool = False,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    request_job: Optional[Union[GraphDefinition, JobDefinition]] = None,
    request_jobs: Optional[Sequence[Union[GraphDefinition, JobDefinition]]] = None,
) -> Callable[
    [Callable[[RunFailureSensorContext], Union[SkipReason, PipelineRunReaction]]],
    SensorDefinition,
]:
    """
    Creates a sensor that reacts to job failure events, where the decorated function will be
    run when a run fails.

    Takes a :py:class:`~dagster.RunFailureSensorContext`.

    Args:
        name (Optional[str]): The name of the job failure sensor. Defaults to the name of the
            decorated function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        monitored_jobs (Optional[List[Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition, RepositorySelector, JobSelector]]]):
            The jobs in the current repository that will be monitored by this failure sensor.
            Defaults to None, which means the alert will be sent when any job in the current
            repository fails.
        monitor_all_repositories (bool): If set to True, the sensor will monitor all runs in the
            Dagster instance. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.
        job_selection (Optional[List[Union[JobDefinition, GraphDefinition, RepositorySelector, JobSelector]]]):
            (deprecated in favor of monitored_jobs) The jobs in the current repository that will be
            monitored by this failure sensor. Defaults to None, which means the alert will be sent
            when any job in the repository fails.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
        request_job (Optional[Union[GraphDefinition, JobDefinition]]): The job a RunRequest should
            execute if yielded from the sensor.
        request_jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition]]]): (experimental)
            A list of jobs to be executed if RunRequests are yielded from the sensor.
    """

    def inner(
        fn: Callable[[RunFailureSensorContext], Union[SkipReason, PipelineRunReaction]]
    ) -> SensorDefinition:
        check.callable_param(fn, "fn")
        if name is None or callable(name):
            sensor_name = fn.__name__
        else:
            sensor_name = name

        if job_selection:
            deprecation_warning("job_selection", "2.0.0", "Use monitored_jobs instead.")
        jobs = monitored_jobs if monitored_jobs else job_selection

        @run_status_sensor(
            run_status=DagsterRunStatus.FAILURE,
            name=sensor_name,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            monitored_jobs=jobs,
            monitor_all_repositories=monitor_all_repositories,
            default_status=default_status,
            request_job=request_job,
            request_jobs=request_jobs,
        )
        def _run_failure_sensor(context: RunStatusSensorContext):
            return fn(context.for_run_failure())

        return _run_failure_sensor

    # This case is for when decorator is used bare, without arguments
    if callable(name):
        return inner(name)

    return inner


class RunStatusSensorDefinition(SensorDefinition):
    """
    Define a sensor that reacts to a given status of pipeline execution, where the decorated
    function will be evaluated when a run is at the given status.

    Args:
        name (str): The name of the sensor. Defaults to the name of the decorated function.
        run_status (DagsterRunStatus): The status of a run which will be
            monitored by the sensor.
        run_status_sensor_fn (Callable[[RunStatusSensorContext], Union[SkipReason, PipelineRunReaction]]): The core
            evaluation function for the sensor. Takes a :py:class:`~dagster.RunStatusSensorContext`.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        monitored_jobs (Optional[List[Union[JobDefinition, GraphDefinition, UnresolvedAssetJobDefinition, JobSelector, RepositorySelector]]]):
            The jobs in the current repository that will be monitored by this sensor. Defaults to
            None, which means the alert will be sent when any job in the repository fails.
        monitor_all_repositories (bool): If set to True, the sensor will monitor all runs in the
            Dagster instance. If set to True, an error will be raised if you also specify
            monitored_jobs or job_selection. Defaults to False.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
        request_job (Optional[Union[GraphDefinition, JobDefinition]]): The job a RunRequest should
            execute if yielded from the sensor.
        request_jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition]]]): (experimental)
            A list of jobs to be executed if RunRequests are yielded from the sensor.
    """

    def __init__(
        self,
        name: str,
        run_status: DagsterRunStatus,
        run_status_sensor_fn: Callable[[RunStatusSensorContext], RawSensorEvaluationFunctionReturn],
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        monitored_jobs: Optional[
            Sequence[
                Union[
                    PipelineDefinition,
                    GraphDefinition,
                    UnresolvedAssetJobDefinition,
                    "RepositorySelector",
                    "JobSelector",
                ]
            ]
        ] = None,
        monitor_all_repositories: bool = False,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        request_job: Optional[Union[GraphDefinition, JobDefinition]] = None,
        request_jobs: Optional[Sequence[Union[GraphDefinition, JobDefinition]]] = None,
    ):

        from dagster._core.event_api import RunShardedEventsCursor
        from dagster._core.host_representation.selector import JobSelector, RepositorySelector
        from dagster._core.storage.event_log.base import EventRecordsFilter

        check.str_param(name, "name")
        check.inst_param(run_status, "run_status", DagsterRunStatus)
        check.callable_param(run_status_sensor_fn, "run_status_sensor_fn")
        check.opt_int_param(minimum_interval_seconds, "minimum_interval_seconds")
        check.opt_str_param(description, "description")
        check.opt_list_param(
            monitored_jobs,
            "monitored_jobs",
            (
                PipelineDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                RepositorySelector,
                JobSelector,
            ),
        )
        check.inst_param(default_status, "default_status", DefaultSensorStatus)

        self._run_status_sensor_fn = check.callable_param(
            run_status_sensor_fn, "run_status_sensor_fn"
        )
        event_type = PIPELINE_RUN_STATUS_TO_EVENT_TYPE[run_status]

        def _wrapped_fn(context: SensorEvaluationContext):
            # initiate the cursor to (most recent event id, current timestamp) when:
            # * it's the first time starting the sensor
            # * or, the cursor isn't in valid format (backcompt)
            if context.cursor is None or not RunStatusSensorCursor.is_valid(context.cursor):
                most_recent_event_records = list(
                    context.instance.get_event_records(
                        EventRecordsFilter(event_type=event_type), ascending=False, limit=1
                    )
                )
                most_recent_event_id = (
                    most_recent_event_records[0].storage_id
                    if len(most_recent_event_records) == 1
                    else -1
                )

                new_cursor = RunStatusSensorCursor(
                    update_timestamp=pendulum.now("UTC").isoformat(),
                    record_id=most_recent_event_id,
                )
                context.update_cursor(new_cursor.to_json())
                yield SkipReason(f"Initiating {name}. Set cursor to {new_cursor}")
                return

            record_id, update_timestamp = RunStatusSensorCursor.from_json(context.cursor)

            # Fetch events after the cursor id
            # * we move the cursor forward to the latest visited event's id to avoid revisits
            # * when the daemon is down, bc we persist the cursor info, we can go back to where we
            #   left and backfill alerts for the qualified events (up to 5 at a time) during the downtime
            # Note: this is a cross-run query which requires extra handling in sqlite, see details in SqliteEventLogStorage.
            event_records = context.instance.get_event_records(
                EventRecordsFilter(
                    after_cursor=RunShardedEventsCursor(
                        id=record_id,
                        run_updated_after=cast(datetime, pendulum.parse(update_timestamp)),
                    ),
                    event_type=event_type,
                ),
                ascending=True,
                limit=5,
            )

            # split monitored_jobs into external repos, external jobs, and jobs in the current repo
            other_repos = (
                [x for x in monitored_jobs if isinstance(x, RepositorySelector)]
                if monitored_jobs
                else []
            )
            other_repo_jobs = (
                [x for x in monitored_jobs if isinstance(x, JobSelector)] if monitored_jobs else []
            )

            current_repo_jobs = (
                [x for x in monitored_jobs if not isinstance(x, (JobSelector, RepositorySelector))]
                if monitored_jobs
                else []
            )

            for event_record in event_records:
                event_log_entry = event_record.event_log_entry
                storage_id = event_record.storage_id

                # get run info
                run_records = context.instance.get_run_records(
                    filters=RunsFilter(run_ids=[event_log_entry.run_id])
                )

                # skip if we couldn't find the right run
                if len(run_records) != 1:
                    # bc we couldn't find the run, we use the event timestamp as the approximate
                    # run update timestamp
                    approximate_update_timestamp = utc_datetime_from_timestamp(
                        event_log_entry.timestamp
                    )
                    context.update_cursor(
                        RunStatusSensorCursor(
                            record_id=storage_id,
                            update_timestamp=approximate_update_timestamp.isoformat(),
                        ).to_json()
                    )
                    continue

                pipeline_run = run_records[0].pipeline_run
                update_timestamp = run_records[0].update_timestamp

                job_match = False

                # if monitor_all_repositories is provided, then we want to run the sensor for all jobs in all repositories
                if monitor_all_repositories:
                    job_match = True

                # check if the run is in the current repository and (if provided) one of jobs specified in monitored_jobs
                if (
                    not job_match
                    and
                    # the pipeline has a repository (not manually executed)
                    pipeline_run.external_pipeline_origin
                    and
                    # the pipeline belongs to the current repository
                    pipeline_run.external_pipeline_origin.external_repository_origin.repository_name
                    == context.repository_name
                ):
                    if monitored_jobs:
                        if pipeline_run.pipeline_name in map(lambda x: x.name, current_repo_jobs):
                            job_match = True
                    else:
                        job_match = True

                if not job_match:
                    # check if the run is one of the jobs specified by JobSelector or RepositorySelector (ie in another repo)
                    # make a JobSelector for the run in question
                    external_repository_origin = check.not_none(
                        pipeline_run.external_pipeline_origin
                    ).external_repository_origin
                    run_job_selector = JobSelector(
                        location_name=external_repository_origin.repository_location_origin.location_name,
                        repository_name=external_repository_origin.repository_name,
                        job_name=pipeline_run.pipeline_name,
                    )
                    if run_job_selector in other_repo_jobs:
                        job_match = True

                    # make a RepositorySelector for the run in question
                    run_repo_selector = RepositorySelector(
                        location_name=external_repository_origin.repository_location_origin.location_name,
                        repository_name=external_repository_origin.repository_name,
                    )
                    if run_repo_selector in other_repos:
                        job_match = True

                if not job_match:
                    # the run in question doesn't match any of the criteria for we advance the cursor and move on
                    context.update_cursor(
                        RunStatusSensorCursor(
                            record_id=storage_id, update_timestamp=update_timestamp.isoformat()
                        ).to_json()
                    )
                    continue

                serializable_error = None

                try:
                    with user_code_error_boundary(
                        RunStatusSensorExecutionError,
                        lambda: f'Error occurred during the execution sensor "{name}".',
                    ):
                        # one user code invocation maps to one failure event
                        sensor_return = run_status_sensor_fn(
                            RunStatusSensorContext(
                                sensor_name=name,
                                dagster_run=pipeline_run,
                                dagster_event=event_log_entry.dagster_event,
                                instance=context.instance,
                            )
                        )
                        if sensor_return is not None:
                            context.update_cursor(
                                RunStatusSensorCursor(
                                    record_id=storage_id,
                                    update_timestamp=update_timestamp.isoformat(),
                                ).to_json()
                            )

                            if isinstance(
                                sensor_return, (RunRequest, SkipReason, PipelineRunReaction)
                            ):
                                yield sensor_return
                            else:
                                yield from sensor_return
                            return
                except RunStatusSensorExecutionError as run_status_sensor_execution_error:
                    # When the user code errors, we report error to the sensor tick not the original run.
                    serializable_error = serializable_error_info_from_exc_info(
                        run_status_sensor_execution_error.original_exc_info
                    )

                context.update_cursor(
                    RunStatusSensorCursor(
                        record_id=storage_id, update_timestamp=update_timestamp.isoformat()
                    ).to_json()
                )

                # Yield PipelineRunReaction to indicate the execution success/failure.
                # The sensor machinery would
                # * report back to the original run if success
                # * update cursor and job state
                yield PipelineRunReaction(
                    pipeline_run=pipeline_run,
                    run_status=run_status,
                    error=serializable_error,
                )

        super(RunStatusSensorDefinition, self).__init__(
            name=name,
            evaluation_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            default_status=default_status,
            job=request_job,
            jobs=request_jobs,
        )

    def __call__(self, *args, **kwargs):
        if is_context_provided(self._run_status_sensor_fn):
            if len(args) + len(kwargs) == 0:
                raise DagsterInvalidInvocationError(
                    "Run status sensor function expected context argument, but no context argument "
                    "was provided when invoking."
                )
            if len(args) + len(kwargs) > 1:
                raise DagsterInvalidInvocationError(
                    "Run status sensor invocation received multiple arguments. Only a first "
                    "positional context parameter should be provided when invoking."
                )

            context_param_name = get_function_params(self._run_status_sensor_fn)[0].name

            if args:
                context = check.opt_inst_param(args[0], context_param_name, RunStatusSensorContext)
            else:
                if context_param_name not in kwargs:
                    raise DagsterInvalidInvocationError(
                        f"Run status sensor invocation expected argument '{context_param_name}'."
                    )
                context = check.opt_inst_param(
                    kwargs[context_param_name], context_param_name, RunStatusSensorContext
                )

            if not context:
                raise DagsterInvalidInvocationError(
                    "Context must be provided for direct invocation of run status sensor."
                )

            return self._run_status_sensor_fn(context)

        else:
            if len(args) + len(kwargs) > 0:
                raise DagsterInvalidInvocationError(
                    "Run status sensor decorated function has no arguments, but arguments were "
                    "provided to invocation."
                )

            return self._run_status_sensor_fn()


def run_status_sensor(
    run_status: DagsterRunStatus,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    monitored_jobs: Optional[
        Sequence[
            Union[
                PipelineDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
            ]
        ]
    ] = None,
    job_selection: Optional[
        Sequence[
            Union[
                PipelineDefinition,
                GraphDefinition,
                UnresolvedAssetJobDefinition,
                "RepositorySelector",
                "JobSelector",
            ]
        ]
    ] = None,
    monitor_all_repositories: bool = False,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    request_job: Optional[Union[GraphDefinition, JobDefinition]] = None,
    request_jobs: Optional[Sequence[Union[GraphDefinition, JobDefinition]]] = None,
) -> Callable[
    [Callable[[RunStatusSensorContext], RawSensorEvaluationFunctionReturn]],
    RunStatusSensorDefinition,
]:
    """
    Creates a sensor that reacts to a given status of pipeline execution, where the decorated
    function will be run when a pipeline is at the given status.

    Takes a :py:class:`~dagster.RunStatusSensorContext`.

    Args:
        run_status (DagsterRunStatus): The status of run execution which will be
            monitored by the sensor.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        monitored_jobs (Optional[List[Union[PipelineDefinition, GraphDefinition, UnresolvedAssetJobDefinition, RepositorySelector, JobSelector]]]):
            Jobs in the current repository that will be monitored by this sensor. Defaults to None, which means the alert will
            be sent when any job in the repository matches the requested run_status. Jobs in external repositories can be monitored by using
            RepositorySelector or JobSelector.
        monitor_all_repositories (bool): If set to True, the sensor will monitor all runs in the Dagster instance.
            If set to True, an error will be raised if you also specify monitored_jobs or job_selection.
            Defaults to False.
        job_selection (Optional[List[Union[PipelineDefinition, GraphDefinition, RepositorySelector, JobSelector]]]):
            (deprecated in favor of monitored_jobs) Jobs in the current repository that will be
            monitored by this sensor. Defaults to None, which means the alert will be sent when
            any job in the repository matches the requested run_status.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
        request_job (Optional[Union[GraphDefinition, JobDefinition]]): The job that should be
            executed if a RunRequest is yielded from the sensor.
        request_jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition]]]): (experimental)
            A list of jobs to be executed if RunRequests are yielded from the sensor.
    """

    def inner(
        fn: Callable[["RunStatusSensorContext"], RawSensorEvaluationFunctionReturn]
    ) -> RunStatusSensorDefinition:

        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        if job_selection:
            deprecation_warning("job_selection", "2.0.0", "Use monitored_jobs instead.")
        jobs = monitored_jobs if monitored_jobs else job_selection

        if jobs and monitor_all_repositories:
            DagsterInvalidDefinitionError(
                f"Cannot specify both monitor_all_repositories and {'monitored_jobs' if monitored_jobs else 'job_selection'}."
            )

        return RunStatusSensorDefinition(
            name=sensor_name,
            run_status=run_status,
            run_status_sensor_fn=fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            monitored_jobs=jobs,
            monitor_all_repositories=monitor_all_repositories,
            default_status=default_status,
            request_job=request_job,
            request_jobs=request_jobs,
        )

    return inner
