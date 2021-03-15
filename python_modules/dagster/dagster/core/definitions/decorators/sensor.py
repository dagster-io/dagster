import inspect
from typing import TYPE_CHECKING, Callable, List, Optional, Union

from dagster import check
from dagster.core.definitions.sensor import RunRequest, SensorDefinition, SkipReason
from dagster.core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from dagster.core.definitions.sensor import SensorExecutionContext


def sensor(
    pipeline_name: str,
    name: Optional[str] = None,
    solid_selection: Optional[List[str]] = None,
    mode: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
) -> Callable[
    [Callable[["SensorExecutionContext"], Union[SkipReason, RunRequest]]], SensorDefinition
]:
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
        pipeline_name (str): Name of the target pipeline
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated
            function.
        solid_selection (Optional[List[str]]): A list of solid subselection (including single
            solid names) to execute for runs for this sensor e.g.
            ``['*some_solid+', 'other_solid']``
        mode (Optional[str]): The mode to apply when executing runs for this sensor.
            (default: 'default')
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
    """
    check.opt_str_param(name, "name")

    def inner(
        fn: Callable[["SensorExecutionContext"], Union[SkipReason, RunRequest]]
    ) -> SensorDefinition:
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
            description=description,
        )

    return inner
