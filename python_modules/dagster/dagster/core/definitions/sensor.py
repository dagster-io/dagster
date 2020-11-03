from collections import namedtuple

from dagster import check
from dagster.core.definitions.job import JobContext, JobDefinition, JobType
from dagster.core.instance import DagsterInstance
from dagster.serdes import whitelist_for_serdes
from dagster.utils import ensure_gen
from dagster.utils.backcompat import experimental_class_warning


@whitelist_for_serdes
class SensorSkipData(namedtuple("_SensorSkipData", "skip_message")):
    def __new__(cls, skip_message=None):
        return super(SensorSkipData, cls).__new__(
            cls, skip_message=check.opt_str_param(skip_message, "skip_message")
        )


@whitelist_for_serdes
class SensorRunParams(namedtuple("_SensorRunParams", "execution_key run_config tags")):
    """
    Represents all the information required to launch a single run instigated by a sensor body.
    Must be returned by a SensorDefinition's evaluation function for a run to be launched.

    Attributes:
        execution_key (str | None): A string key to identify this launched run. The sensor will
            ensure that exactly one run is created for each execution key, and will not create
            another run if the same execution key is requested in a later evaluation.  Passing in
            a `None` value means that the sensor will attempt to create and launch every run
            requested for every sensor evaluation.
        run_config (Optional[Dict]): The environment config that parameterizes the run execution to
            be launched, as a dict.
        tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
            to the launched run.
    """

    def __new__(cls, execution_key, run_config=None, tags=None):
        return super(SensorRunParams, cls).__new__(
            cls,
            run_config=check.opt_dict_param(run_config, "run_config"),
            tags=check.opt_dict_param(tags, "tags"),
            execution_key=check.opt_str_param(execution_key, "execution_key"),
        )


class SensorExecutionContext(JobContext):
    """Sensor execution context.

    An instance of this class is made available as the first argument to the evaluation function
    on SensorDefinition.

    Attributes:
        instance (DagsterInstance): The instance configured to run the schedule
        last_completion_time (float): The last time that the sensor was evaluated (UTC).
    """

    __slots__ = ["_last_completion_time"]

    def __init__(self, instance, last_completion_time):
        super(SensorExecutionContext, self).__init__(
            check.inst_param(instance, "instance", DagsterInstance),
        )
        self._last_completion_time = check.opt_float_param(
            last_completion_time, "last_completion_time"
        )

    @property
    def last_completion_time(self):
        return self._last_completion_time


class SensorDefinition(JobDefinition):
    """Define a sensor that initiates a set of job runs

    Args:
        name (str): The name of the sensor to create.
        pipeline_name (str): The name of the pipeline to execute when the sensor fires.
        evaluation_fn (Callable[[SensorExecutionContext]]): The core evaluation function for the
            sensor, which is run at an interval to determine whether a run should be launched or
            not. Takes a :py:class:`~dagster.SensorExecutionContext`.

            This function must return a generator, which must yield either a single SensorSkipData
            or one or more SensorRunParams objects.
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
        experimental_class_warning("SensorDefinition")
        super(SensorDefinition, self).__init__(
            name,
            job_type=JobType.SENSOR,
            pipeline_name=pipeline_name,
            mode=mode,
            solid_selection=solid_selection,
        )
        self._evaluation_fn = check.callable_param(evaluation_fn, "evaluation_fn")

    def get_tick_data(self, context):
        check.inst_param(context, "context", SensorExecutionContext)
        result = list(ensure_gen(self._evaluation_fn(context)))

        if not result or result == [None]:
            return []

        if len(result) == 1:
            return check.is_list(result, of_type=(SensorRunParams, SensorSkipData))

        return check.is_list(result, of_type=SensorRunParams)
