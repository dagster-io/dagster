import inspect
from contextlib import ExitStack

from dagster import check
from dagster.core.errors import DagsterInvariantViolationError
from dagster.core.instance import DagsterInstance
from dagster.core.instance.ref import InstanceRef
from dagster.utils import ensure_gen

from .job import JobType, RunRequest, SkipReason
from .mode import DEFAULT_MODE_NAME
from .utils import check_valid_name

DEFAULT_SENSOR_DAEMON_INTERVAL = 30


class SensorExecutionContext:
    """Sensor execution context.

    An instance of this class is made available as the first argument to the evaluation function
    on SensorDefinition.

    Attributes:
        instance_ref (InstanceRef): The serialized instance configured to run the schedule
        last_completion_time (float): The last time that the sensor was evaluated (UTC).
        last_run_key (str): The run key of the RunRequest most recently created by this sensor.
    """

    __slots__ = [
        "_instance_ref",
        "_last_completion_time",
        "_last_run_key",
        "_exit_stack",
        "_instance",
    ]

    def __init__(self, instance_ref, last_completion_time, last_run_key):
        self._exit_stack = ExitStack()
        self._instance = None

        self._instance_ref = check.inst_param(instance_ref, "instance_ref", InstanceRef)
        self._last_completion_time = check.opt_float_param(
            last_completion_time, "last_completion_time"
        )
        self._last_run_key = check.opt_str_param(last_run_key, "last_run_key")

        self._instance = None

    def __enter__(self):
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()

    @property
    def instance(self):
        if not self._instance:
            self._instance = self._exit_stack.enter_context(
                DagsterInstance.from_ref(self._instance_ref)
            )
        return self._instance

    @property
    def last_completion_time(self):
        return self._last_completion_time

    @property
    def last_run_key(self):
        return self._last_run_key


class SensorDefinition:
    """Define a sensor that initiates a set of runs based on some external state

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
        mode (Optional[str]): The mode to apply when executing runs triggered by this sensor.
            (default: 'default')
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
    """

    __slots__ = [
        "_name",
        "_pipeline_name",
        "_tags_fn",
        "_run_config_fn",
        "_mode",
        "_solid_selection",
        "_description",
        "_evaluation_fn",
        "_min_interval",
    ]

    def __init__(
        self,
        name,
        pipeline_name,
        evaluation_fn,
        solid_selection=None,
        mode=None,
        minimum_interval_seconds=None,
        description=None,
    ):

        self._name = check_valid_name(name)
        self._pipeline_name = check.str_param(pipeline_name, "pipeline_name")
        self._mode = check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME)
        self._solid_selection = check.opt_nullable_list_param(
            solid_selection, "solid_selection", of_type=str
        )
        self._description = check.opt_str_param(description, "description")
        self._evaluation_fn = check.callable_param(evaluation_fn, "evaluation_fn")
        self._min_interval = check.opt_int_param(
            minimum_interval_seconds, "minimum_interval_seconds", DEFAULT_SENSOR_DAEMON_INTERVAL
        )

    @property
    def name(self):
        return self._name

    @property
    def pipeline_name(self):
        return self._pipeline_name

    @property
    def job_type(self):
        return JobType.SENSOR

    @property
    def solid_selection(self):
        return self._solid_selection

    @property
    def mode(self):
        return self._mode

    @property
    def description(self):
        return self._description

    def get_execution_data(self, context):
        check.inst_param(context, "context", SensorExecutionContext)
        result = list(ensure_gen(self._evaluation_fn(context)))

        if not result or result == [None]:
            return []

        if len(result) == 1:
            return check.is_list(result, of_type=(RunRequest, SkipReason))

        return check.is_list(result, of_type=RunRequest)

    @property
    def minimum_interval_seconds(self):
        return self._min_interval


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
