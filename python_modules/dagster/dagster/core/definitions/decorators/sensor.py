import inspect

from dagster import check
from dagster.core.definitions.sensor import SensorDefinition, SensorRunParams, SensorSkipData
from dagster.core.errors import DagsterInvariantViolationError
from dagster.utils.backcompat import experimental


@experimental
def sensor(pipeline_name, name=None, solid_selection=None, mode=None):
    """
    Creates a sensor where the decorated function is used as the sensor's evaluation function.  The
    decorated function may:

    1. Return a `SensorRunParams` object.
    2. Yield a number of `SensorRunParams` objects.
    3. Return a `SensorSkipData` object, providing a descriptive message of why no runs were
       requested.
    4. Yield nothing (skipping without providing a reason)

    Takes a :py:class:`~dagster.SensorExecutionContext`.

    Args:
        name (str): The name of this sensor
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

        def _wrapped_fn(context):
            result = fn(context)

            if inspect.isgenerator(result):
                for item in result:
                    yield item
            elif isinstance(result, (SensorSkipData, SensorRunParams)):
                yield result

            elif result is not None:
                raise DagsterInvariantViolationError(
                    (
                        "Error in sensor {sensor_name}: Sensor unexpectedly returned output "
                        "{result} of type {type_}.  Should only return SensorSkipData or "
                        "SensorRunParams objects."
                    ).format(sensor_name=sensor_name, result=result, type_=type(result))
                )

        return SensorDefinition(
            name=sensor_name,
            pipeline_name=pipeline_name,
            evaluation_fn=_wrapped_fn,
            solid_selection=solid_selection,
            mode=mode,
        )

    return inner
