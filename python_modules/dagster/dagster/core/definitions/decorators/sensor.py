from dagster import check
from dagster.core.definitions.sensor import SensorDefinition
from dagster.utils.backcompat import experimental


@experimental
def sensor(
    pipeline_name, name=None, run_config_fn=None, tags_fn=None, solid_selection=None, mode=None,
):
    """
    The decorated function will be called to determine whether the provided job should execute,
    taking a :py:class:`~dagster.core.definitions.sensor.SensorExecutionContext`
    as its only argument, returning a boolean if the execution should fire

    Args:
        name (str): The name of this sensor
        run_config_fn (Optional[Callable[[SensorExecutionContext], Optional[Dict]]]): A function
            that takes a SensorExecutionContext object and returns the environment configuration
            that parameterizes this execution, as a dict.
        tags_fn (Optional[Callable[[SensorExecutionContext], Optional[Dict[str, str]]]]): A function
            that generates tags to attach to the sensor runs. Takes a
            :py:class:`~dagster.SensorExecutionContext` and returns a dictionary of tags (string
            key-value pairs).
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute for runs for this sensor e.g.
            ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing runs for this sensor.
            (default: 'default')
    """
    check.opt_str_param(name, "name")

    def inner(fn):
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        return SensorDefinition(
            name=sensor_name,
            pipeline_name=pipeline_name,
            should_execute=fn,
            run_config_fn=run_config_fn,
            tags_fn=tags_fn,
            solid_selection=solid_selection,
            mode=mode,
        )

    return inner
