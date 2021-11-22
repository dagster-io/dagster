import inspect
from functools import update_wrapper
from typing import TYPE_CHECKING, Callable, Generator, List, Optional, Sequence, Union

from dagster import check
from dagster.core.definitions.sensor_definition import RunRequest, SensorDefinition, SkipReason
from dagster.core.errors import DagsterInvariantViolationError

from ...errors import DagsterInvariantViolationError
from ..events import AssetKey
from ..graph_definition import GraphDefinition
from ..job_definition import JobDefinition
from ..sensor_definition import (
    AnyAssetSensorDefinition,
    AssetSensorDefinition,
    MultiAssetSensorDefinition,
    RunRequest,
    SensorDefinition,
    SensorEvaluationContext,
    SkipReason,
)

if TYPE_CHECKING:
    from ...events.log import EventLogEntry


def sensor(
    pipeline_name: Optional[str] = None,
    name: Optional[str] = None,
    solid_selection: Optional[List[str]] = None,
    mode: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[Union[GraphDefinition, JobDefinition]] = None,
    jobs: Optional[Sequence[Union[GraphDefinition, JobDefinition]]] = None,
) -> Callable[
    [
        Callable[
            [SensorEvaluationContext],
            Union[Generator[Union[RunRequest, SkipReason], None, None], RunRequest, SkipReason],
        ]
    ],
    SensorDefinition,
]:
    """
    Creates a sensor where the decorated function is used as the sensor's evaluation function.  The
    decorated function may:

    1. Return a `RunRequest` object.
    2. Yield multiple of `RunRequest` objects.
    3. Return or yield a `SkipReason` object, providing a descriptive message of why no runs were
       requested.
    4. Return or yield nothing (skipping without providing a reason)

    Takes a :py:class:`~dagster.SensorEvaluationContext`.

    Args:
        pipeline_name (Optional[str]): (legacy) Name of the target pipeline. Cannot be used in
            conjunction with `job` or `jobs` parameters.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated
            function.
        solid_selection (Optional[List[str]]): (legacy) A list of solid subselection (including single
            solid names) to execute for runs for this sensor e.g.
            ``['*some_solid+', 'other_solid']``.
            Cannot be used in conjunction with `job` or `jobs` parameters.
        mode (Optional[str]): (legacy) The mode to apply when executing runs for this sensor. Cannot be used
            in conjunction with `job` or `jobs` parameters.
            (default: 'default')
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition]]): The job to be executed when the sensor fires.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition]]]): (experimental) A list of jobs to be executed when the sensor fires.
    """
    check.opt_str_param(name, "name")

    def inner(
        fn: Callable[
            ["SensorEvaluationContext"],
            Union[Generator[Union[SkipReason, RunRequest], None, None], SkipReason, RunRequest],
        ]
    ) -> SensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        sensor_def = SensorDefinition(
            name=sensor_name,
            pipeline_name=pipeline_name,
            evaluation_fn=fn,
            solid_selection=solid_selection,
            mode=mode,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
        )

        update_wrapper(sensor_def, wrapped=fn)

        return sensor_def

    return inner


def asset_sensor(
    asset_key: AssetKey,
    pipeline_name: Optional[str] = None,
    name: Optional[str] = None,
    solid_selection: Optional[List[str]] = None,
    mode: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[Union[GraphDefinition, JobDefinition]] = None,
    jobs: Optional[Sequence[Union[GraphDefinition, JobDefinition]]] = None,
) -> Callable[
    [
        Callable[
            [
                "SensorEvaluationContext",
                "EventLogEntry",
            ],
            Union[Generator[Union[RunRequest, SkipReason], None, None], RunRequest, SkipReason],
        ]
    ],
    AssetSensorDefinition,
]:
    """
    Creates an asset sensor where the decorated function is used as the asset sensor's evaluation
    function.  The decorated function may:

    1. Return a `RunRequest` object.
    2. Yield multiple of `RunRequest` objects.
    3. Return or yield a `SkipReason` object, providing a descriptive message of why no runs were
       requested.
    4. Return or yield nothing (skipping without providing a reason)

    Takes a :py:class:`~dagster.SensorEvaluationContext` and an EventLogEntry corresponding to an
    AssetMaterialization event.

    Args:
        asset_key (AssetKey): The asset_key this sensor monitors.
        pipeline_name (Optional[str]): (legacy) Name of the target pipeline. Cannot be used in conjunction with `job` or `jobs` parameters.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated
            function.
        solid_selection (Optional[List[str]]): (legacy) A list of solid subselection (including single
            solid names) to execute for runs for this sensor e.g.
            ``['*some_solid+', 'other_solid']``. Cannot be used in conjunction with `job` or `jobs`
            parameters.
        mode (Optional[str]): (legacy) The mode to apply when executing runs for this sensor. Cannot be used
            in conjunction with `job` or `jobs` parameters.
            (default: 'default')
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition]]): The job to be executed when the sensor fires.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition]]]): (experimental) A list of jobs to be executed when the sensor fires.
    """

    check.opt_str_param(name, "name")

    def inner(
        fn: Callable[
            [
                "SensorEvaluationContext",
                "EventLogEntry",
            ],
            Union[Generator[Union[SkipReason, RunRequest], None, None], SkipReason, RunRequest],
        ]
    ) -> AssetSensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        def _wrapped_fn(context, event):
            result = fn(context, event)

            if inspect.isgenerator(result):
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
            pipeline_name=pipeline_name,
            asset_materialization_fn=_wrapped_fn,
            solid_selection=solid_selection,
            mode=mode,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
        )

    return inner


def multi_asset_sensor(
    asset_keys: List[AssetKey],
    job: Optional[Union[GraphDefinition, JobDefinition]] = None,
    jobs: Optional[Sequence[Union[GraphDefinition, JobDefinition]]] = None,
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
):
    """
    Creates an asset sensor that is evaluated whenever all of the assets it depends on have been
    updated.

    The decorated function is used as the asset sensor's evaluation function. The decorated
    function may:

    1. Return a :py:class:`~dagster.RunRequest` object.
    2. Yield multiple :py:class:`~dagster.RunRequest` objects.
    3. Return or yield a a :py:class:`~dagster.SkipReason` object, providing a descriptive message
        explaining why no runs were requested.
    4. Return or yield ``None`` (skipping without providing a reason)

    Takes a :py:class:`~dagster.SensorEvaluationContext` and an EventLogEntry corresponding to an
    AssetMaterialization event.

    May only be used with the :py:func:`@op <dagster.op>` API (not the legacy
    :py:func:`@pipeline <dagster.pipeline>` APIs).

    Args:
        asset_keys (List[AssetKey]): The asset keys this sensor monitors.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated
            function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition]]): The job to be executed when the
            sensor fires.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition]]]): (experimental) A list of
            jobs to be executed when the sensor fires.
    """

    check.opt_str_param(name, "name")

    def inner(
        fn: Callable[
            [
                "SensorEvaluationContext",
                "EventLogEntry",
            ],
            Union[Generator[Union[SkipReason, RunRequest], None, None], SkipReason, RunRequest],
        ]
    ) -> MultiAssetSensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        def _wrapped_fn(context, event):
            result = fn(context, event)

            if inspect.isgenerator(result):
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
            job=job,
            jobs=jobs,
            asset_materialization_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
        )

    return inner


def any_asset_sensor(
    asset_keys: List[AssetKey],
    name: Optional[str] = None,
    minimum_interval_seconds: Optional[int] = None,
    description: Optional[str] = None,
    job: Optional[Union[GraphDefinition, JobDefinition]] = None,
    jobs: Optional[Sequence[Union[GraphDefinition, JobDefinition]]] = None,
):
    """
    Creates an asset sensor that is evaluated whenever any of the assets it depends on have been
    updated.

    The decorated function is used as the asset sensor's evaluation function. The decorated
    function may:

    1. Return a :py:class:`~dagster.RunRequest` object.
    2. Yield multiple :py:class:`~dagster.RunRequest` objects.
    3. Return or yield a a :py:class:`~dagster.SkipReason` object, providing a descriptive message
        explaining why no runs were requested.
    4. Return or yield ``None`` (skipping without providing a reason)

    Takes a :py:class:`~dagster.SensorEvaluationContext` and an EventLogEntry corresponding to an
    AssetMaterialization event.

    May only be used with the :py:func:`@op <dagster.op>` API (not the legacy
    :py:func:`@pipeline <dagster.pipeline>` APIs).

    Args:
        asset_keys (List[AssetKey]): The asset keys this sensor monitors.
        name (Optional[str]): The name of the sensor. Defaults to the name of the decorated
            function.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition]]): The job to be executed when the
            sensor fires.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition]]]): (experimental) A list of
            jobs to be executed when the sensor fires.
    """

    check.opt_str_param(name, "name")

    def inner(
        fn: Callable[
            [
                "SensorEvaluationContext",
                "EventLogEntry",
            ],
            Union[Generator[Union[SkipReason, RunRequest], None, None], SkipReason, RunRequest],
        ]
    ) -> AnyAssetSensorDefinition:
        check.callable_param(fn, "fn")
        sensor_name = name or fn.__name__

        def _wrapped_fn(context, event):
            result = fn(context, event)

            if inspect.isgenerator(result):
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

        return AnyAssetSensorDefinition(
            name=sensor_name,
            asset_keys=asset_keys,
            job=job,
            jobs=jobs,
            asset_materialization_fn=_wrapped_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
        )

    return inner
