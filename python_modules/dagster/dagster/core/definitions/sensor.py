import inspect

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.instance import DagsterInstance
from dagster.utils import ensure_gen

from .job import JobContext, JobDefinition, JobType, RunRequest, SkipReason


class SensorExecutionContext(JobContext):
    """Sensor execution context.

    An instance of this class is made available as the first argument to the evaluation function
    on SensorDefinition.

    Attributes:
        instance (DagsterInstance): The instance configured to run the schedule
        last_completion_time (float): The last time that the sensor was evaluated (UTC).
        last_run_key (str): The run key of the RunRequest most recently created by this sensor.
    """

    __slots__ = ["_last_completion_time", "_last_run_key"]

    def __init__(self, instance, last_completion_time, last_run_key):
        super(SensorExecutionContext, self).__init__(
            check.inst_param(instance, "instance", DagsterInstance),
        )
        self._last_completion_time = check.opt_float_param(
            last_completion_time, "last_completion_time"
        )
        self._last_run_key = check.opt_str_param(last_run_key, "last_run_key")

    @property
    def last_completion_time(self):
        return self._last_completion_time

    @property
    def last_run_key(self):
        return self._last_run_key


class SensorDefinition(JobDefinition):
    """Define a sensor that initiates a set of job runs

    Args:
        name (str): The name of the sensor to create.
        pipeline_name (str): The name of the pipeline to execute when the sensor fires.
        evaluation_fn (Callable[[SensorExecutionContext]]): The core evaluation function for the
            sensor, which is run at an interval to determine whether a run should be launched or
            not. Takes a :py:class:`~dagster.SensorExecutionContext`.

            This function must return a generator, which must yield either a single SkipReason
            or one or more RunRequest objects.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the sensor runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing this sensor. (default: 'default')
    """

    __slots__ = [
        "_evaluation_fn",
    ]

    def __init__(
        self, name, pipeline_name, evaluation_fn, solid_selection=None, mode=None,
    ):
        super(SensorDefinition, self).__init__(
            name,
            job_type=JobType.SENSOR,
            pipeline_name=pipeline_name,
            mode=mode,
            solid_selection=solid_selection,
        )
        self._evaluation_fn = check.callable_param(evaluation_fn, "evaluation_fn")

    def get_execution_data(self, context):
        check.inst_param(context, "context", SensorExecutionContext)
        result = list(ensure_gen(self._evaluation_fn(context)))

        if not result or result == [None]:
            return []

        if len(result) == 1:
            return check.is_list(result, of_type=(RunRequest, SkipReason))

        return check.is_list(result, of_type=RunRequest)


def wrap_sensor_evaluation(sensor_name, result):
    if inspect.isgenerator(result):
        for item in result:
            yield item

    elif isinstance(result, (SkipReason, RunRequest)):
        yield result

    elif result is not None:
        raise DagsterInvariantViolationError(
            f"Error in sensor {sensor_name}: Sensor unexpectedly returned output "
            f"{result} of type {type(result)}.  Should only return SkipReason or "
            "RunRequest objects."
        )
