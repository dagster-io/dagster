import collections.abc
import inspect
from functools import update_wrapper
from typing import Any, Callable, Optional, Sequence, Set, Union

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_selection import AssetSelection

from ...errors import DagsterInvariantViolationError
from ..asset_sensor_definition import AssetSensorDefinition
from ..events import AssetKey
from ..multi_asset_sensor_definition import (
    AssetMaterializationFunction,
    MultiAssetMaterializationFunction,
    MultiAssetSensorDefinition,
)
from ..run_request import SensorResult
from ..sensor_definition import (
    DefaultSensorStatus,
    RawSensorEvaluationFunction,
    RunRequest,
    SensorDefinition,
    SkipReason,
)
from ..target import ExecutableDefinition


def sensor(
    job_name: Optional[str] = None,
    *,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[ExecutableDefinition] = None,
    jobs: Optional[Sequence[ExecutableDefinition]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    asset_selection: Optional[AssetSelection] = None,
    required_resource_keys: Optional[Set[str]] = None,
) -> Callable[[RawSensorEvaluationFunction], SensorDefinition]:
    """Creates a sensor where the decorated function is used as the sensor's evaluation function.

    The decorated function may:

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
        asset_selection (AssetSelection): (Experimental) an asset selection to launch a run for if
            the sensor condition is met. This can be provided instead of specifying a job.
    """
    check.opt_str_param(name, "name")

    def inner(fn: RawSensorEvaluationFunction) -> SensorDefinition:
        check.callable_param(fn, "fn")

        sensor_def = SensorDefinition.dagster_internal_init(
            name=name,
            job_name=job_name,
            evaluation_fn=fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
            asset_selection=asset_selection,
            required_resource_keys=required_resource_keys,
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
    """Creates an asset sensor where the decorated function is used as the asset sensor's evaluation
    function.

    The decorated function may:

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

        def _wrapped_fn(*args, **kwargs) -> Any:
            result = fn(*args, **kwargs)

            if inspect.isgenerator(result) or isinstance(result, list):
                for item in result:
                    yield item
            elif isinstance(result, (RunRequest, SkipReason)):
                yield result

            elif isinstance(result, SensorResult):
                if result.cursor:
                    raise DagsterInvariantViolationError(
                        f"Error in asset sensor {sensor_name}: Sensor returned a SensorResult"
                        " with a cursor value. The cursor is managed by the asset sensor and"
                        " should not be modified by a user."
                    )
                yield result

            elif result is not None:
                raise DagsterInvariantViolationError(
                    (
                        "Error in sensor {sensor_name}: Sensor unexpectedly returned output "
                        "{result} of type {type_}.  Should only return SkipReason or "
                        "RunRequest objects."
                    ).format(sensor_name=sensor_name, result=result, type_=type(result))
                )

        # Preserve any resource arguments from the underlying function, for when we inspect the
        # wrapped function later on
        _wrapped_fn.__signature__ = inspect.signature(fn)

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


@experimental
def multi_asset_sensor(
    monitored_assets: Union[Sequence[AssetKey], AssetSelection],
    *,
    job_name: Optional[str] = None,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[ExecutableDefinition] = None,
    jobs: Optional[Sequence[ExecutableDefinition]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    request_assets: Optional[AssetSelection] = None,
) -> Callable[[MultiAssetMaterializationFunction,], MultiAssetSensorDefinition,]:
    """Creates an asset sensor that can monitor multiple assets.

    The decorated function is used as the asset sensor's evaluation
    function.  The decorated function may:

    1. Return a `RunRequest` object.
    2. Return a list of `RunRequest` objects.
    3. Return a `SkipReason` object, providing a descriptive message of why no runs were requested.
    4. Return nothing (skipping without providing a reason)
    5. Yield a `SkipReason` or yield one or more `RunRequest` objects.

    Takes a :py:class:`~dagster.MultiAssetSensorEvaluationContext`.

    Args:
        monitored_assets (Union[Sequence[AssetKey], AssetSelection]): The assets this
            sensor monitors. If an AssetSelection object is provided, it will only apply to assets
            within the Definitions that this sensor is part of.
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
        request_assets (Optional[AssetSelection]): (Experimental) an asset selection to launch a run
            for if the sensor condition is met. This can be provided instead of specifying a job.
    """
    check.opt_str_param(name, "name")

    if not isinstance(monitored_assets, AssetSelection) and not (
        isinstance(monitored_assets, collections.abc.Sequence)
        and all(isinstance(el, AssetKey) for el in monitored_assets)
    ):
        check.failed(
            "The value passed to monitored_assets param must be either an AssetSelection"
            f" or a Sequence of AssetKeys, but was a {type(monitored_assets)}"
        )

    def inner(fn: MultiAssetMaterializationFunction) -> MultiAssetSensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        sensor_def = MultiAssetSensorDefinition(
            name=sensor_name,
            monitored_assets=monitored_assets,
            job_name=job_name,
            asset_materialization_fn=fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
            request_assets=request_assets,
        )
        update_wrapper(sensor_def, wrapped=fn)
        return sensor_def

    return inner
