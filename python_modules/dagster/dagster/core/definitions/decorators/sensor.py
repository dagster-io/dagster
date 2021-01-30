import inspect

from dagster import check
from dagster.core.definitions.sensor import RunRequest, SensorDefinition, SkipReason
from dagster.core.errors import DagsterInvariantViolationError


def sensor(
    pipeline_name, name=None, solid_selection=None, mode=None, minimum_interval_seconds=None
):
    """
    Creates a sensor where the decorated function is used as the sensor's evaluation function.  The
    decorated function may:

    1. Return a `RunRequest` object.
    2. Yield multiple of `RunRequest` objects.
    3. Return or yield a `SkipReason` object, providing a descriptive message of why no runs were
       requested.
    4. Return or yield nothing (skipping without providing a reason)

    Takes a :py:class:`~dagster.SensorExecutionContext`.

    Args:
        name (str): The name of this sensor
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute for runs for this sensor e.g.
            ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing runs for this sensor.
            (default: 'default')
        minimum_interval_seconds (Optional[str]): The minimum number of seconds that will elapse
            between sensor evaluations.  Practically, the time elapsed between sensor evaluations
            will be the shortest multiple of the sensor daemon evaluation interval (30 seconds) that
            is greater than or equal to this value.
    """
    check.opt_str_param(name, "name")

    def inner(fn):
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        def _wrapped_fn(context):
            result = fn(context)

            if inspect.isgenerator(result):
                for item in result:
                    yield item
            elif isinstance(result, (SkipReason, RunRequest)):
                yield result

            elif result is not None:
                raise DagsterInvariantViolationError(
                    (
                        "Error in sensor {sensor_name}: Sensor unexpectedly returned output "
                        "{result} of type {type_}.  Should only return SkipReason or "
                        "RunRequest objects."
                    ).format(sensor_name=sensor_name, result=result, type_=type(result))
                )

        return SensorDefinition(
            name=sensor_name,
            pipeline_name=pipeline_name,
            evaluation_fn=_wrapped_fn,
            solid_selection=solid_selection,
            mode=mode,
            minimum_interval_seconds=minimum_interval_seconds,
        )

    return inner
