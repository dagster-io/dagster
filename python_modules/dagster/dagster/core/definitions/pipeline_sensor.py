from typing import Callable, List, NamedTuple, Optional, Union, cast

import pendulum
from dagster import check
from dagster.core.definitions.sensor import (
    PipelineRunReaction,
    SensorDefinition,
    SensorEvaluationContext,
    SkipReason,
)
from dagster.core.errors import PipelineSensorExecutionError, user_code_error_boundary
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunsFilter
from dagster.serdes import (
    deserialize_json_to_dagster_namedtuple,
    serialize_dagster_namedtuple,
    whitelist_for_serdes,
)
from dagster.serdes.errors import DeserializationError
from dagster.seven import JSONDecodeError
from dagster.utils.error import serializable_error_info_from_exc_info


class PipelineFailureSensorContext(
    NamedTuple(
        "_PipelineFailureSensorContext",
        [("sensor_name", str), ("pipeline_run", PipelineRun), ("failure_event", DagsterEvent)],
    )
):
    """The ``context`` object available to a decorated function of ``pipeline_failure_sensor``.

    Attributes:
        sensor_name (str): the name of the sensor.
        pipeline_run (PipelineRun): the failed pipeline run.
        failure_event (DagsterEvent): the pipeline failure event.
    """

    def __new__(cls, sensor_name, pipeline_run, failure_event):

        return super(PipelineFailureSensorContext, cls).__new__(
            cls,
            sensor_name=check.str_param(sensor_name, "sensor_name"),
            pipeline_run=check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            failure_event=check.inst_param(failure_event, "failure_event", DagsterEvent),
        )


@whitelist_for_serdes
class PipelineFailureSensorCursor(
    NamedTuple(
        "_PipelineFailureSensorCursor",
        [("record_id", int), ("update_timestamp", str)],
    )
):
    def __new__(cls, record_id, update_timestamp):

        return super(PipelineFailureSensorCursor, cls).__new__(
            cls,
            record_id=check.int_param(record_id, "record_id"),
            update_timestamp=check.str_param(update_timestamp, "update_timestamp"),
        )

    @staticmethod
    def is_valid(json_str: str) -> bool:
        try:
            obj = deserialize_json_to_dagster_namedtuple(json_str)
            return isinstance(obj, PipelineFailureSensorCursor)
        except (JSONDecodeError, DeserializationError):
            return False

    def to_json(self) -> str:
        return serialize_dagster_namedtuple(cast(NamedTuple, self))

    @staticmethod
    def from_json(json_str: str) -> tuple:
        return deserialize_json_to_dagster_namedtuple(json_str)


def pipeline_failure_sensor(
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    pipeline_selection: Optional[List[str]] = None,
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
    """

    from dagster.core.storage.event_log.base import RunShardedEventsCursor, EventRecordsFilter

    dagster_event_type = DagsterEventType.PIPELINE_FAILURE

    def inner(
        fn: Callable[["PipelineFailureSensorContext"], Union[SkipReason, PipelineRunReaction]]
    ) -> SensorDefinition:
        check.callable_param(fn, "fn")
        if name is None or callable(name):
            sensor_name = fn.__name__
        else:
            sensor_name = name

        def _wrapped_fn(context: SensorEvaluationContext):
            # initiate the cursor to (most recent event id, current timestamp) when:
            # * it's the first time starting the sensor
            # * or, the cursor isn't in valid format (backcompt)
            if context.cursor is None or not PipelineFailureSensorCursor.is_valid(context.cursor):
                most_recent_event_records = list(
                    context.instance.get_event_records(ascending=False, limit=1)
                )
                most_recent_event_id = (
                    most_recent_event_records[0].storage_id
                    if len(most_recent_event_records) == 1
                    else -1
                )

                new_cursor = PipelineFailureSensorCursor(
                    update_timestamp=pendulum.now("UTC").isoformat(),
                    record_id=most_recent_event_id,
                )
                context.update_cursor(new_cursor.to_json())
                yield SkipReason(f"Initiating {sensor_name}. Set cursor to {new_cursor}")
                return

            record_id, update_timestamp = PipelineFailureSensorCursor.from_json(context.cursor)

            # Fetch failure events after the cursor id
            # * we move the cursor forward to the latest visited event's id to avoid revisits
            # * when the daemon is down, bc we persist the cursor info, we can go back to where we
            #   left and backfill alerts for the qualified events (up to 5 at a time) during the downtime
            # Note: this is a cross-run query which requires extra handling in sqlite, see details in SqliteEventLogStorage.
            event_records = context.instance.get_event_records(
                EventRecordsFilter(
                    after_cursor=RunShardedEventsCursor(
                        id=record_id, run_updated_after=pendulum.parse(update_timestamp)
                    ),
                    event_type=dagster_event_type,
                ),
                ascending=True,
                limit=5,
            )

            for event_record in event_records:
                event_log_entry = event_record.event_log_entry
                storage_id = event_record.storage_id

                # get run info
                run_records = context.instance.get_run_records(
                    filters=PipelineRunsFilter(run_ids=[event_log_entry.run_id])
                )
                check.invariant(len(run_records) == 1)
                pipeline_run = run_records[0].pipeline_run
                update_timestamp = run_records[0].update_timestamp

                # skip if any of of the followings happens:
                if (
                    # the failed pipeline does not have a repository (manually executed)
                    not pipeline_run.external_pipeline_origin
                    or
                    # the failed pipeline does not belong to the current repository
                    pipeline_run.external_pipeline_origin.external_repository_origin.repository_name
                    != context.repository_name
                    or
                    # if pipeline is not selected
                    (pipeline_selection and pipeline_run.pipeline_name not in pipeline_selection)
                ):
                    context.update_cursor(
                        PipelineFailureSensorCursor(
                            record_id=storage_id, update_timestamp=update_timestamp.isoformat()
                        ).to_json()
                    )
                    continue

                serializable_error = None

                try:
                    with user_code_error_boundary(
                        PipelineSensorExecutionError,
                        lambda: f'Error occurred during the execution sensor "{sensor_name}".',
                    ):
                        # one user code invocation maps to one failure event
                        fn(
                            PipelineFailureSensorContext(
                                sensor_name=sensor_name,
                                pipeline_run=pipeline_run,
                                failure_event=event_log_entry.dagster_event,
                            )
                        )
                except PipelineSensorExecutionError as pipeline_sensor_execution_error:
                    # When the user code errors, we report error to the sensor tick not the original run.
                    serializable_error = serializable_error_info_from_exc_info(
                        pipeline_sensor_execution_error.original_exc_info
                    )

                context.update_cursor(
                    PipelineFailureSensorCursor(
                        record_id=storage_id, update_timestamp=update_timestamp.isoformat()
                    ).to_json()
                )

                # Yield PipelineRunReaction to indicate the execution success/failure.
                # The sensor machinery would
                # * report back to the original run if success
                # * update cursor and job state
                yield PipelineRunReaction(
                    pipeline_run=pipeline_run,
                    error=serializable_error,
                )

        return SensorDefinition(
            name=sensor_name,
            evaluation_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
        )

    # This case is for when decorator is used bare, without arguments, i.e. @pipeline_failure_sensor
    if callable(name):
        return inner(name)

    return inner
