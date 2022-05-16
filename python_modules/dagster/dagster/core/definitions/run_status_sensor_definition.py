import warnings
from datetime import datetime
from typing import Any, Callable, List, NamedTuple, Optional, Union, cast

import pendulum

import dagster._check as check
from dagster.core.definitions import GraphDefinition, PipelineDefinition
from dagster.core.definitions.sensor_definition import (
    DefaultSensorStatus,
    PipelineRunReaction,
    SensorDefinition,
    SensorEvaluationContext,
    SkipReason,
    is_context_provided,
)
from dagster.core.errors import (
    DagsterInvalidInvocationError,
    RunStatusSensorExecutionError,
    user_code_error_boundary,
)
from dagster.core.events import PIPELINE_RUN_STATUS_TO_EVENT_TYPE, DagsterEvent
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import DagsterRun, PipelineRun, PipelineRunStatus, RunsFilter
from dagster.serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster.serdes.errors import DeserializationError
from dagster.serdes.serdes import register_serdes_tuple_fallbacks
from dagster.seven import JSONDecodeError
from dagster.utils import utc_datetime_from_timestamp
from dagster.utils.error import serializable_error_info_from_exc_info

from ..decorator_utils import get_function_params


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
            ("sensor_name", str),
            ("dagster_run", DagsterRun),
            ("dagster_event", DagsterEvent),
            ("instance", DagsterInstance),
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

    def for_pipeline_failure(self):
        return PipelineFailureSensorContext(
            sensor_name=self.sensor_name,
            dagster_run=self.dagster_run,
            dagster_event=self.dagster_event,
            instance=self.instance,
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


class PipelineFailureSensorContext(RunStatusSensorContext):
    """The ``context`` object available to a decorated function of ``pipeline_failure_sensor``.

    Attributes:
        sensor_name (str): the name of the sensor.
        pipeline_run (PipelineRun): the failed pipeline run.
        failure_event (DagsterEvent): the pipeline failure event.
    """

    @property
    def failure_event(self):
        return self.dagster_event


class RunFailureSensorContext(RunStatusSensorContext):
    """The ``context`` object available to a decorated function of ``run_failure_sensor``.

    Attributes:
        sensor_name (str): the name of the sensor.
        pipeline_run (PipelineRun): the failed pipeline run.
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


def pipeline_failure_sensor(
    name: Optional[Union[Callable[..., Any], str]] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    pipeline_selection: Optional[List[str]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> Callable[
    [Callable[[PipelineFailureSensorContext], Union[SkipReason, PipelineRunReaction]]],
    SensorDefinition,
]:
    """
    Creates a sensor that reacts to pipeline failure events, where the decorated function will be
    run when a pipeline run fails.

    Takes a :py:class:`~dagster.PipelineFailureSensorContext`.

    Args:
        name (Optional[str]): The name of the pipeline failure sensor. Defaults to the name of the
            decorated function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        pipeline_selection (Optional[List[str]]): Names of the pipelines that will be monitored by
            this failure sensor. Defaults to None, which means the alert will be sent when any
            pipeline in the repository fails.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    def inner(
        fn: Callable[[PipelineFailureSensorContext], Union[SkipReason, PipelineRunReaction]]
    ) -> SensorDefinition:
        check.callable_param(fn, "fn")
        if name is None or callable(name):
            sensor_name = fn.__name__
        else:
            sensor_name = name

        @run_status_sensor(
            pipeline_run_status=PipelineRunStatus.FAILURE,
            pipeline_selection=pipeline_selection,
            name=sensor_name,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            default_status=default_status,
        )
        def _pipeline_failure_sensor(context: RunStatusSensorContext):
            fn(context.for_pipeline_failure())

        return _pipeline_failure_sensor

    # This case is for when decorator is used bare, without arguments, i.e. @pipeline_failure_sensor
    if callable(name):
        return inner(name)

    return inner


def run_failure_sensor(
    name: Optional[Union[Callable[..., Any], str]] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job_selection: Optional[List[Union[PipelineDefinition, GraphDefinition]]] = None,
    pipeline_selection: Optional[List[str]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
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
        job_selection (Optional[List[Union[JobDefinition, GraphDefinition]]]): The jobs that
            will be monitored by this failure sensor. Defaults to None, which means the alert will
            be sent when any job in the repository fails.
        pipeline_selection (Optional[List[str]]): (legacy) Names of the pipelines that will be monitored by
            this sensor. Defaults to None, which means the alert will be sent when any pipeline in
            the repository fails.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    def inner(
        fn: Callable[[RunFailureSensorContext], Union[SkipReason, PipelineRunReaction]]
    ) -> SensorDefinition:
        check.callable_param(fn, "fn")
        if name is None or callable(name):
            sensor_name = fn.__name__
        else:
            sensor_name = name

        @run_status_sensor(
            pipeline_run_status=PipelineRunStatus.FAILURE,
            name=sensor_name,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job_selection=job_selection,
            pipeline_selection=pipeline_selection,
            default_status=default_status,
        )
        def _run_failure_sensor(context: RunStatusSensorContext):
            fn(context.for_run_failure())

        return _run_failure_sensor

    # This case is for when decorator is used bare, without arguments, i.e. @pipeline_failure_sensor
    if callable(name):
        return inner(name)

    return inner


class RunStatusSensorDefinition(SensorDefinition):
    """
    Define a sensor that reacts to a given status of pipeline execution, where the decorated
    function will be evaluated when a run is at the given status.

    Args:
        name (str): The name of the sensor. Defaults to the name of the decorated function.
        pipeline_run_status (PipelineRunStatus): The status of a run which will be
            monitored by the sensor.
        run_status_sensor_fn (Callable[[RunStatusSensorContext], Union[SkipReason, PipelineRunReaction]]): The core
            evaluation function for the sensor. Takes a :py:class:`~dagster.RunStatusSensorContext`.
        pipeline_selection (Optional[List[str]]): (legacy) Names of the pipelines that will be monitored by
            this sensor. Defaults to None, which means the alert will be sent when any pipeline in
            the repository fails.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job_selection (Optional[List[Union[JobDefinition, GraphDefinition]]]): The jobs that
            will be monitored by this sensor. Defaults to None, which means the alert will be sent
            when any job in the repository fails.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    def __init__(
        self,
        name: str,
        pipeline_run_status: PipelineRunStatus,
        run_status_sensor_fn: Callable[
            [RunStatusSensorContext], Union[SkipReason, PipelineRunReaction]
        ],
        pipeline_selection: Optional[List[str]] = None,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job_selection: Optional[List[Union[PipelineDefinition, GraphDefinition]]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    ):

        from dagster.core.storage.event_log.base import EventRecordsFilter, RunShardedEventsCursor

        check.str_param(name, "name")
        check.inst_param(pipeline_run_status, "pipeline_run_status", PipelineRunStatus)
        check.callable_param(run_status_sensor_fn, "run_status_sensor_fn")
        check.opt_list_param(pipeline_selection, "pipeline_selection", str)
        check.opt_int_param(minimum_interval_seconds, "minimum_interval_seconds")
        check.opt_str_param(description, "description")
        check.opt_list_param(job_selection, "job_selection", (PipelineDefinition, GraphDefinition))
        check.inst_param(default_status, "default_status", DefaultSensorStatus)

        self._run_status_sensor_fn = check.callable_param(
            run_status_sensor_fn, "run_status_sensor_fn"
        )
        event_type = PIPELINE_RUN_STATUS_TO_EVENT_TYPE[pipeline_run_status]

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

                # skip if any of of the followings happens:
                if (
                    # the pipeline does not have a repository (manually executed)
                    not pipeline_run.external_pipeline_origin
                    or
                    # the pipeline does not belong to the current repository
                    pipeline_run.external_pipeline_origin.external_repository_origin.repository_name
                    != context.repository_name
                    or
                    # if pipeline is not selected
                    (pipeline_selection and pipeline_run.pipeline_name not in pipeline_selection)
                    or
                    # if job not selected
                    (
                        job_selection
                        and pipeline_run.pipeline_name not in map(lambda x: x.name, job_selection)
                    )
                ):
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
                        run_status_sensor_fn(
                            RunStatusSensorContext(
                                sensor_name=name,
                                dagster_run=pipeline_run,
                                dagster_event=event_log_entry.dagster_event,
                                instance=context.instance,
                            )
                        )
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
                    run_status=pipeline_run_status,
                    error=serializable_error,
                )

        super(RunStatusSensorDefinition, self).__init__(
            name=name,
            evaluation_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            default_status=default_status,
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
    pipeline_run_status: PipelineRunStatus,
    pipeline_selection: Optional[List[str]] = None,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job_selection: Optional[List[Union[PipelineDefinition, GraphDefinition]]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> Callable[
    [Callable[[RunStatusSensorContext], Union[SkipReason, PipelineRunReaction]]],
    RunStatusSensorDefinition,
]:
    """
    Creates a sensor that reacts to a given status of pipeline execution, where the decorated
    function will be run when a pipeline is at the given status.

    Takes a :py:class:`~dagster.RunStatusSensorContext`.

    Args:
        pipeline_run_status (PipelineRunStatus): The status of pipeline execution which will be
            monitored by the sensor.
        pipeline_selection (Optional[List[str]]): Names of the pipelines that will be monitored by
            this sensor. Defaults to None, which means the alert will be sent when any pipeline in
            the repository fails.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job_selection (Optional[List[Union[PipelineDefinition, GraphDefinition]]]): Jobs that will
            be monitored by this sensor. Defaults to None, which means the alert will be sent when
            any job in the repository fails.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    def inner(
        fn: Callable[["RunStatusSensorContext"], Union[SkipReason, PipelineRunReaction]]
    ) -> RunStatusSensorDefinition:

        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        def _wrapped_fn(context: RunStatusSensorContext):
            fn(context)

        return RunStatusSensorDefinition(
            name=sensor_name,
            pipeline_run_status=pipeline_run_status,
            run_status_sensor_fn=_wrapped_fn,
            pipeline_selection=pipeline_selection,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job_selection=job_selection,
            default_status=default_status,
        )

    return inner
