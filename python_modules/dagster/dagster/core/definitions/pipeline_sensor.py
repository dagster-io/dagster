from collections import namedtuple
from datetime import datetime
from typing import Callable, Optional, Union

import pendulum
from dagster import check
from dagster.core.definitions.sensor import (
    PipelineRunReaction,
    SensorDefinition,
    SensorExecutionContext,
    SkipReason,
)
from dagster.core.errors import PipelineSensorExecutionError, user_code_error_boundary
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus, PipelineRunsFilter
from dagster.utils.error import serializable_error_info_from_exc_info


class PipelineFailureSensorContext(
    namedtuple("_PipelineFailureSensorContext", "sensor_name pipeline_run failure_event")
):
    def __new__(cls, sensor_name, pipeline_run, failure_event):

        return super(PipelineFailureSensorContext, cls).__new__(
            cls,
            sensor_name=check.str_param(sensor_name, "sensor_name"),
            pipeline_run=check.inst_param(pipeline_run, "pipeline_run", PipelineRun),
            failure_event=check.inst_param(failure_event, "failure_event", DagsterEvent),
        )


def pipeline_failure_sensor(
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
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
    """

    # TODO: allow multiple types: +DagsterEventType.PIPELINE_INIT_FAILURE
    dagster_event_type = DagsterEventType.PIPELINE_FAILURE

    def inner(
        fn: Callable[["PipelineFailureSensorContext"], Union[SkipReason, PipelineRunReaction]]
    ) -> SensorDefinition:
        check.callable_param(fn, "fn")
        if name is None or callable(name):
            sensor_name = fn.__name__
        else:
            sensor_name = name

        def _wrapped_fn(context: SensorExecutionContext):
            # Initiate the cursor to be the current datetime in UTC first time init (cursor is None)
            if context.cursor is None:
                curr_time = pendulum.now("UTC").isoformat()
                context.update_cursor(curr_time)
                yield SkipReason(
                    f"Initiating {sensor_name}. Set cursor to {datetime.fromisoformat(curr_time)}"
                )
                return

            # Fetch runs where the statuses were updated after the cursor time
            # * we move the cursor forward to the latest visited run's update_timestamp to avoid revisit runs
            # * we filter the query by failure status to reduce the number of scanned rows
            # * when the daemon is down, bc we persist the cursor info, we can go back to where we
            #   left and backfill alerts for the qualified runs (up to 5 at a time) during the downtime
            run_records = context.instance.get_run_records(
                filters=PipelineRunsFilter(
                    statuses=[PipelineRunStatus.FAILURE],
                    updated_after=datetime.fromisoformat(context.cursor),
                ),
                limit=5,
                order_by="update_timestamp",
                ascending=True,
            )

            if len(run_records) == 0:
                yield SkipReason(
                    f"No qualified runs found (no runs updated after {datetime.fromisoformat(context.cursor)})"
                )
                return

            for record in run_records:
                pipeline_run = record.pipeline_run
                update_timestamp = record.update_timestamp
                events = context.instance.all_logs(pipeline_run.run_id, dagster_event_type)

                if len(events) == 0:
                    context.update_cursor(update_timestamp.isoformat())
                    continue

                check.invariant(
                    len(events) == 1, "get more than one PIPELINE_FAILURE event for one given run."
                )

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
                                failure_event=events[0].dagster_event,
                            )
                        )
                except PipelineSensorExecutionError as pipeline_sensor_execution_error:
                    # When the user code errors, we report error to the sensor tick not the original run.
                    serializable_error = serializable_error_info_from_exc_info(
                        pipeline_sensor_execution_error.original_exc_info
                    )

                context.update_cursor(update_timestamp.isoformat())

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
