import inspect
from typing import Any, Callable, NamedTuple, Optional, Sequence, Set

import dagster._check as check
from dagster._annotations import public
from dagster._core.decorator_utils import get_function_params
from dagster._core.definitions.resource_annotation import get_resource_args

from .events import AssetKey
from .run_request import RunRequest, SkipReason
from .sensor_definition import (
    DefaultSensorStatus,
    RawSensorEvaluationFunctionReturn,
    SensorDefinition,
    SensorType,
    validate_and_get_resource_dict,
)
from .target import ExecutableDefinition
from .utils import check_valid_name


class AssetSensorParamNames(NamedTuple):
    context_param_name: Optional[str]
    event_log_entry_param_name: Optional[str]


def get_asset_sensor_param_names(fn: Callable) -> AssetSensorParamNames:
    """Determines the names of the context and event log entry parameters for an asset sensor function.
    These are assumed to be the first two non-resource params, in order (context param before event log entry).
    """
    resource_params = {param.name for param in get_resource_args(fn)}

    non_resource_params = [
        param.name for param in get_function_params(fn) if param.name not in resource_params
    ]

    context_param_name = non_resource_params[0] if len(non_resource_params) > 0 else None
    event_log_entry_param_name = non_resource_params[1] if len(non_resource_params) > 1 else None

    return AssetSensorParamNames(
        context_param_name=context_param_name, event_log_entry_param_name=event_log_entry_param_name
    )


class AssetSensorDefinition(SensorDefinition):
    """Define an asset sensor that initiates a set of runs based on the materialization of a given
    asset.

    If the asset has been materialized multiple times between since the last sensor tick, the
    evaluation function will only be invoked once, with the latest materialization.

    Args:
        name (str): The name of the sensor to create.
        asset_key (AssetKey): The asset_key this sensor monitors.
        asset_materialization_fn (Callable[[SensorEvaluationContext, EventLogEntry], Union[Iterator[Union[RunRequest, SkipReason]], RunRequest, SkipReason]]): The core
            evaluation function for the sensor, which is run at an interval to determine whether a
            run should be launched or not. Takes a :py:class:`~dagster.SensorEvaluationContext` and
            an EventLogEntry corresponding to an AssetMaterialization event.

            This function must return a generator, which must yield either a single SkipReason
            or one or more RunRequest objects.
        minimum_interval_seconds (Optional[int]): The minimum number of seconds that will elapse
            between sensor evaluations.
        description (Optional[str]): A human-readable description of the sensor.
        job (Optional[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]): The job
            object to target with this sensor.
        jobs (Optional[Sequence[Union[GraphDefinition, JobDefinition, UnresolvedAssetJobDefinition]]]):
            (experimental) A list of jobs to be executed when the sensor fires.
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
    """

    def __init__(
        self,
        name: str,
        asset_key: AssetKey,
        job_name: Optional[str],
        asset_materialization_fn: Callable[
            ...,
            RawSensorEvaluationFunctionReturn,
        ],
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        job: Optional[ExecutableDefinition] = None,
        jobs: Optional[Sequence[ExecutableDefinition]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        required_resource_keys: Optional[Set[str]] = None,
    ):
        self._asset_key = check.inst_param(asset_key, "asset_key", AssetKey)

        from dagster._core.events import DagsterEventType
        from dagster._core.storage.event_log.base import EventRecordsFilter

        resource_arg_names: Set[str] = {
            arg.name for arg in get_resource_args(asset_materialization_fn)
        }

        combined_required_resource_keys = (
            check.opt_set_param(required_resource_keys, "required_resource_keys", of_type=str)
            | resource_arg_names
        )

        def _wrap_asset_fn(materialization_fn) -> Any:
            def _fn(context) -> Any:
                after_cursor = None
                if context.cursor:
                    try:
                        after_cursor = int(context.cursor)
                    except ValueError:
                        after_cursor = None

                event_records = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=self._asset_key,
                        after_cursor=after_cursor,
                    ),
                    ascending=False,
                    limit=1,
                )

                if not event_records:
                    yield SkipReason(
                        f"No new materialization events found for asset key {self._asset_key}"
                    )
                    return

                event_record = event_records[0]

                (
                    context_param_name,
                    event_log_entry_param_name,
                ) = get_asset_sensor_param_names(materialization_fn)

                resource_args_populated = validate_and_get_resource_dict(
                    context.resources, name, resource_arg_names
                )

                # Build asset sensor function args, which can include any subset of
                # context arg, event log entry arg, and any resource args
                args = resource_args_populated
                if context_param_name:
                    args[context_param_name] = context
                if event_log_entry_param_name:
                    args[event_log_entry_param_name] = event_record.event_log_entry

                result = materialization_fn(**args)
                if inspect.isgenerator(result) or isinstance(result, list):
                    for item in result:
                        yield item
                elif isinstance(result, (SkipReason, RunRequest)):
                    yield result
                context.update_cursor(str(event_record.storage_id))

            return _fn

        super(AssetSensorDefinition, self).__init__(
            name=check_valid_name(name),
            job_name=job_name,
            evaluation_fn=_wrap_asset_fn(
                check.callable_param(asset_materialization_fn, "asset_materialization_fn"),
            ),
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=job,
            jobs=jobs,
            default_status=default_status,
            required_resource_keys=combined_required_resource_keys,
        )

    @public
    @property
    def asset_key(self) -> AssetKey:
        """AssetKey: The key of the asset targeted by this sensor."""
        return self._asset_key

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.ASSET
