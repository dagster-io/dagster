from dagster import check
from dagster.core.definitions.job import JobContext, JobDefinition, JobType
from dagster.core.instance import DagsterInstance
from dagster.utils.backcompat import experimental_class_warning


class SensorExecutionContext(JobContext):
    """Sensor execution context.

    An instance of this class is made available as the first argument to the `should_execute`
    function on SensorDefinition.

    Attributes:
        instance (DagsterInstance): The instance configured to run the schedule
        last_evaluation_time (float): The last time that the sensor was evaluated (UTC).
    """

    __slots__ = ["_last_evaluation_time"]

    def __init__(self, instance, last_evaluation_time):
        super(SensorExecutionContext, self).__init__(
            check.inst_param(instance, "instance", DagsterInstance),
        )
        self._last_evaluation_time = check.opt_float_param(
            last_evaluation_time, "last_evaluation_time"
        )

    @property
    def last_evaluation_time(self):
        return self._last_evaluation_time


class SensorDefinition(JobDefinition):
    """Define a sensor that initiates a set of job runs

    Args:
        name (str): The name of the sensor to create.
        pipeline_name (str): The name of the pipeline to execute when the sensor fires.
        should_execute (Callable[[SensorExecutionContext], bool]): A function that runs
            at an interval to determine whether a run should be launched or not. Takes a
            :py:class:`~dagster.SensorExecutionContext` and returns a boolean (``True`` if the
            sensor should execute).
        run_config_fn (Callable[[SensorExecutionContext], [Dict]]): A function that takes a
            SensorExecutionContext object and returns the environment configuration that
            parameterizes this execution, as a dict.
        tags_fn (Optional[Callable[[SensorExecutionContext], Optional[Dict[str, str]]]]): A
            function that generates tags to attach to the sensors runs. Takes a
            :py:class:`~dagster.SensorExecutionContext` and returns a dictionary of tags (string
            key-value pairs).
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute when the sensor runs. e.g. ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing this sensor. (default: 'default')
    """

    __slots__ = [
        "_run_config_fn",
        "_tags_fn",
        "_should_execute",
    ]

    def __init__(
        self,
        name,
        pipeline_name,
        should_execute,
        run_config_fn=None,
        tags_fn=None,
        solid_selection=None,
        mode=None,
    ):
        experimental_class_warning("SensorDefinition")
        super(SensorDefinition, self).__init__(
            name,
            job_type=JobType.SENSOR,
            pipeline_name=pipeline_name,
            mode=mode,
            solid_selection=solid_selection,
        )
        self._should_execute = check.callable_param(should_execute, "should_execute")
        self._run_config_fn = check.opt_callable_param(
            run_config_fn, "run_config_fn", default=lambda _context: {}
        )
        self._tags_fn = check.opt_callable_param(tags_fn, "tags_fn", default=lambda _context: {})

    def get_run_config(self, context):
        check.inst_param(context, "context", SensorExecutionContext)
        return self._run_config_fn(context)

    def get_tags(self, context):
        check.inst_param(context, "context", SensorExecutionContext)
        return self._tags_fn(context)

    def should_execute(self, context):
        check.inst_param(context, "context", SensorExecutionContext)
        return self._should_execute(context)
