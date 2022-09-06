import inspect
from functools import update_wrapper
from typing import TYPE_CHECKING, Callable, Optional, Sequence, Union, TypeVar, List

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.errors import DagsterInvariantViolationError

from ...errors import DagsterInvariantViolationError
from ..events import AssetKey
from ..sensor_definition import (
    AssetMaterializationFunction,
    AssetSensorDefinition,
    DefaultSensorStatus,
    MultiAssetMaterializationFunction,
    MultiAssetSensorDefinition,
    AssetMaterializationFunctionReturn,
    RawSensorEvaluationFunction,
    RawSensorEvaluationFunctionReturn,
    RunRequest,
    SensorDefinition,
    SkipReason,
)
from ..target import ExecutableDefinition

if TYPE_CHECKING:
    from ...events.log import EventLogEntry


def sensor(
    job_name: Optional[str] = None,
    *,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[ExecutableDefinition] = None,
    jobs: Optional[Sequence[ExecutableDefinition]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> Callable[[RawSensorEvaluationFunction], SensorDefinition]:
    """
    Creates a sensor where the decorated function is used as the sensor's evaluation function.  The
    decorated function may:

    1. Return a `RunRequest` object.
    2. Return a list of `RunRequest` objects.
    3. Return a `SkipReason` object, providing a descriptive message of why no runs were requested.
    4. Return nothing (skipping without providing a reason)
    5. Yield a `SkipReason` or yield one or more `RunRequest` objects.

    Takes a :py:class:`~dagster.SensorEvaluationContext`.

    Args:
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated
            function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]):
            The job to be executed when the sensor fires.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]]):
            (experimental) A list of jobs to be executed when the sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """
    check.opt_str_param(name, "name")

    def inner(fn: RawSensorEvaluationFunction) -> SensorDefinition:
        check.callable_param(fn, "fn")

        sensor_def = SensorDefinition(
            name=name,
            job_name=job_name,
            evaluation_fn=fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
        )

        update_wrapper(sensor_def, wrapped=fn)

        return sensor_def

    return inner


def asset_sensor(
    asset_key: AssetKey,
    *,
    job_name: Optional[str] = None,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[ExecutableDefinition] = None,
    jobs: Optional[Sequence[ExecutableDefinition]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> Callable[[AssetMaterializationFunction,], AssetSensorDefinition,]:
    """
    Creates an asset sensor where the decorated function is used as the asset sensor's evaluation
    function.  The decorated function may:

    1. Return a `RunRequest` object.
    2. Return a list of `RunRequest` objects.
    3. Return a `SkipReason` object, providing a descriptive message of why no runs were requested.
    4. Return nothing (skipping without providing a reason)
    5. Yield a `SkipReason` or yield one or more `RunRequest` objects.

    Takes a :py:class:`~dagster.SensorEvaluationContext` and an EventLogEntry corresponding to an
    AssetMaterialization event.

    Args:
        asset_key (AssetKey): The asset_key this sensor monitors.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated
            function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]): The
            job to be executed when the sensor fires.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]]):
            (experimental) A list of jobs to be executed when the sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.


    Example:

        .. code-block:: python

            from dagster import AssetKey, EventLogEntry, SensorEvaluationContext, asset_sensor


            @asset_sensor(asset_key=AssetKey("my_table"), job=my_job)
            def my_asset_sensor(context: SensorEvaluationContext, asset_event: EventLogEntry):
                return RunRequest(
                    run_key=context.cursor,
                    run_config={
                        "ops": {
                            "read_materialization": {
                                "config": {
                                    "asset_key": asset_event.dagster_event.asset_key.path,
                                }
                            }
                        }
                    },
                )
    """

    check.opt_str_param(name, "name")

    def inner(fn: AssetMaterializationFunction) -> AssetSensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        def _wrapped_fn(context, event):
            result = fn(context, event)

            if inspect.isgenerator(result) or isinstance(result, list):
                for item in result:
                    yield item
            elif isinstance(result, (RunRequest, SkipReason)):
                yield result

            elif result is not None:
                raise DagsterInvariantViolationError(
                    (
                        "Error in sensor {sensor_name}: Sensor unexpectedly returned output "
                        "{result} of type {type_}.  Should only return SkipReason or "
                        "RunRequest objects."
                    ).format(sensor_name=sensor_name, result=result, type_=type(result))
                )

        return AssetSensorDefinition(
            name=sensor_name,
            asset_key=asset_key,
            job_name=job_name,
            asset_materialization_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
        )

    return inner


T = TypeVar("T")


@experimental
def multi_asset_sensor(
    asset_keys: Sequence[AssetKey],
    *,
    job_name: Optional[str] = None,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[ExecutableDefinition] = None,
    jobs: Optional[Sequence[ExecutableDefinition]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
) -> Callable[[MultiAssetMaterializationFunction,], MultiAssetSensorDefinition,]:
    """
    Creates an asset sensor that can monitor multiple assets

    The decorated function is used as the asset sensor's evaluation
    function.  The decorated function may:

    1. Return a `RunRequest` object.
    2. Return a list of `RunRequest` objects.
    3. Return a `SkipReason` object, providing a descriptive message of why no runs were requested.
    4. Return nothing (skipping without providing a reason)
    5. Yield a `SkipReason` or yield one ore more `RunRequest` objects.

    Takes a :py:class:`~dagster.MultiAssetSensorEvaluationContext`.

    Args:
        asset_keys (Sequence[AssetKey]): The asset_keys this sensor monitors.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated
            function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]): The
            job to be executed when the sensor fires.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]]):
            (experimental) A list of jobs to be executed when the sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from Dagit or via the GraphQL API.
    """

    check.opt_str_param(name, "name")

    def inner(fn: MultiAssetMaterializationFunction) -> MultiAssetSensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        def _wrapped_fn(context):
            result = fn(context)

            if inspect.isgenerator(result) or isinstance(result, list):
                for item in result:
                    yield item
            elif isinstance(result, (RunRequest, SkipReason)):
                yield result

            elif result is not None:
                raise DagsterInvariantViolationError(
                    (
                        "Error in sensor {sensor_name}: Sensor unexpectedly returned output "
                        "{result} of type {type_}.  Should only return SkipReason or "
                        "RunRequest objects."
                    ).format(sensor_name=sensor_name, result=result, type_=type(result))
                )

        return MultiAssetSensorDefinition(
            name=sensor_name,
            asset_keys=asset_keys,
            job_name=job_name,
            asset_materialization_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
        )

    return inner
