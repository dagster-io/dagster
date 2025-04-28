import collections.abc
import inspect
from collections.abc import Mapping, Sequence
from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

import dagster._check as check
from dagster._core.definitions.asset_selection import AssetSelection, CoercibleToAssetSelection
from dagster._core.definitions.asset_sensor_definition import AssetSensorDefinition
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.multi_asset_sensor_definition import (
    AssetMaterializationFunction,
    MultiAssetMaterializationFunction,
    MultiAssetSensorDefinition,
)
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    RawSensorEvaluationFunction,
    RunRequest,
    SensorDefinition,
    SkipReason,
)
from dagster._core.definitions.target import ExecutableDefinition
from dagster._core.errors import DagsterInvariantViolationError

if TYPE_CHECKING:
    from dagster._core.definitions.assets import AssetsDefinition
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.unresolved_asset_job_definition import (
        UnresolvedAssetJobDefinition,
    )


def sensor(
    job_name: Optional[str] = None,
    *,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[ExecutableDefinition] = None,
    jobs: Optional[Sequence[ExecutableDefinition]] = None,
    default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
    asset_selection: Optional[CoercibleToAssetSelection] = None,
    required_resource_keys: Optional[set[str]] = None,
    tags: Optional[Mapping[str, str]] = None,
    metadata: Optional[Mapping[str, object]] = None,
    target: Optional[
        Union[
            "CoercibleToAssetSelection",
            "AssetsDefinition",
            "JobDefinition",
            "UnresolvedAssetJobDefinition",
        ]
    ] = None,
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
            A list of jobs to be executed when the sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        asset_selection (Optional[Union[str, Sequence[str], Sequence[AssetKey], Sequence[Union[AssetsDefinition, SourceAsset]], AssetSelection]]):
            An asset selection to launch a run for if the sensor condition is met.
            This can be provided instead of specifying a job.
        tags (Optional[Mapping[str, str]]): A set of key-value tags that annotate the sensor and can
            be used for searching and filtering in the UI.
        metadata (Optional[Mapping[str, object]]): A set of metadata entries that annotate the
            sensor. Values will be normalized to typed `MetadataValue` objects.
        target (Optional[Union[CoercibleToAssetSelection, AssetsDefinition, JobDefinition, UnresolvedAssetJobDefinition]]):
            The target that the sensor will execute.
            It can take :py:class:`~dagster.AssetSelection` objects and anything coercible to it (e.g. `str`, `Sequence[str]`, `AssetKey`, `AssetsDefinition`).
            It can also accept :py:class:`~dagster.JobDefinition` (a function decorated with `@job` is an instance of `JobDefinition`) and `UnresolvedAssetJobDefinition` (the return value of :py:func:`~dagster.define_asset_job`) objects.
            This is a parameter that will replace `job`, `jobs`, and `asset_selection`.
    """
    check.opt_str_param(name, "name")

    def inner(fn: RawSensorEvaluationFunction) -> SensorDefinition:
        check.callable_param(fn, "fn")

        sensor_def = SensorDefinition.dagster_internal_init(
            name=name or fn.__name__,
            job_name=job_name,
            evaluation_fn=fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
            asset_selection=asset_selection,
            required_resource_keys=required_resource_keys,
            tags=tags,
            metadata=metadata,
            target=target,
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
    required_resource_keys: Optional[set[str]] = None,
    tags: Optional[Mapping[str, str]] = None,
    metadata: Optional[Mapping[str, object]] = None,
) -> Callable[
    [
        AssetMaterializationFunction,
    ],
    AssetSensorDefinition,
]:
    """Creates an asset sensor where the decorated function is used as the asset sensor's evaluation
    function.

    If the asset has been materialized multiple times between since the last sensor tick, the
    evaluation function will only be invoked once, with the latest materialization.

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
            A list of jobs to be executed when the sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        tags (Optional[Mapping[str, str]]): A set of key-value tags that annotate the sensor and can
            be used for searching and filtering in the UI. Values that are not already strings will be serialized as JSON.
        metadata (Optional[Mapping[str, object]]): A set of metadata entries that annotate the
            sensor. Values will be normalized to typed `MetadataValue` objects.


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
                yield from result
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
                    f"Error in sensor {sensor_name}: Sensor unexpectedly returned output "
                    f"{result} of type {type(result)}.  Should only return SkipReason or "
                    "RunRequest objects."
                )

        # Preserve any resource arguments from the underlying function, for when we inspect the
        # wrapped function later on
        _wrapped_fn = update_wrapper(_wrapped_fn, wrapped=fn)

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
            required_resource_keys=required_resource_keys,
            tags=tags,
            metadata=metadata,
        )

    return inner


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
    required_resource_keys: Optional[set[str]] = None,
    tags: Optional[Mapping[str, str]] = None,
    metadata: Optional[Mapping[str, object]] = None,
) -> Callable[
    [
        MultiAssetMaterializationFunction,
    ],
    MultiAssetSensorDefinition,
]:
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
            A list of jobs to be executed when the sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        request_assets (Optional[AssetSelection]): An asset selection to launch a run
            for if the sensor condition is met. This can be provided instead of specifying a job.
        tags (Optional[Mapping[str, str]]): A set of key-value tags that annotate the sensor and can
            be used for searching and filtering in the UI.
        metadata (Optional[Mapping[str, object]]): A set of metadata entries that annotate the
            sensor. Values will be normalized to typed `MetadataValue` objects.

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
            required_resource_keys=required_resource_keys,
            tags=tags,
            metadata=metadata,
        )
        update_wrapper(sensor_def, wrapped=fn)
        return sensor_def

    return inner
