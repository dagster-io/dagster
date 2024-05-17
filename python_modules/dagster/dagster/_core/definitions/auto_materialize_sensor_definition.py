import datetime
import logging
from typing import Any, Mapping, Optional, cast

from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.definitions.asset_condition_evaluator import (
    AssetConditionEvaluator,
    AssetConditionEvaluatorArguments,
)
from dagster._core.definitions.asset_selection import CoercibleToAssetSelection
from dagster._core.definitions.data_time import CachingDataTimeResolver
from dagster._core.definitions.data_version import CachingStaleStatusResolver
from dagster._serdes.serdes import deserialize_value
from dagster._utils.caching_instance_queryer import CachingInstanceQueryer

from .asset_selection import AssetSelection
from .sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
    SensorType,
)
from .utils import check_valid_name, normalize_tags


@experimental
class AutoMaterializeSensorDefinition(SensorDefinition):
    """Targets a set of assets and repeatedly evaluates all the AutoMaterializePolicys on all of
    those assets to determine which to request runs for.

    Args:
        name: The name of the sensor.
        asset_selection (Union[str, Sequence[str], Sequence[AssetKey], Sequence[Union[AssetsDefinition, SourceAsset]], AssetSelection]):
            The assets to evaluate AutoMaterializePolicys of and request runs for.
        run_tags: Optional[Mapping[str, Any]] = None,
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        minimum_interval_seconds (Optional[int]): The frequency at which to try to evaluate the
            sensor. The actual interval will be longer if the sensor evaluation takes longer than
            the provided interval.
        description (Optional[str]): A human-readable description of the sensor.
    """

    def __init__(
        self,
        name: str,
        *,
        asset_selection: CoercibleToAssetSelection,
        run_tags: Optional[Mapping[str, Any]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
    ):
        self._run_tags = normalize_tags(run_tags).tags

        def evaluation_fn(context) -> None:
            raise NotImplementedError(
                "Automation policy sensors cannot be evaluated like regular user-space sensors."
            )

        super(AutoMaterializeSensorDefinition, self).__init__(
            name=check_valid_name(name),
            job_name=None,
            evaluation_fn=evaluation_fn,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=None,
            jobs=None,
            default_status=default_status,
            required_resource_keys=None,
            asset_selection=asset_selection,
        )

    @property
    def run_tags(self) -> Mapping[str, str]:
        return self._run_tags

    @property
    def asset_selection(self) -> AssetSelection:
        return cast(AssetSelection, super().asset_selection)

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.AUTO_MATERIALIZE


def _agv_from_context(context: SensorEvaluationContext) -> AssetGraphView:
    asset_graph = check.not_none(context.repository_def).asset_graph
    effective_dt = datetime.datetime.now()
    instance = context.instance

    return AssetGraphView(
        temporal_context=TemporalContext(effective_dt=effective_dt, last_event_id=None),
        stale_resolver=CachingStaleStatusResolver(
            instance=instance,
            instance_queryer=CachingInstanceQueryer(
                instance=instance, asset_graph=asset_graph, evaluation_time=effective_dt
            ),
            asset_graph=asset_graph,
        ),
    )


def _ds_zone_implementation(context: SensorEvaluationContext) -> None:
    asset_graph_view = _agv_from_context(context)

    context_str = check.not_none(context.sensor_type_specific_context_str)
    args = deserialize_value(context_str, AssetConditionEvaluatorArguments)

    evaluator = AssetConditionEvaluator(
        asset_graph=asset_graph_view.asset_graph,
        asset_graph_view=asset_graph_view,
        logger=logging.getLogger(__name__),
        data_time_resolver=CachingDataTimeResolver(
            instance_queryer=asset_graph_view.get_inner_queryer_for_back_compat(),
        ),
        evaluator_arguments=args,
    )

    result = evaluator.evaluate()


@experimental
class DeclarativeSchedulingZone(SensorDefinition):
    """Targets a set of assets and repeatedly evaluates all the AutoMaterializePolicys on all of
    those assets to determine which to request runs for.

    Args:
        name: The name of the sensor.
        asset_selection (Union[str, Sequence[str], Sequence[AssetKey], Sequence[Union[AssetsDefinition, SourceAsset]], AssetSelection]):
            The assets to evaluate AutoMaterializePolicys of and request runs for.
        run_tags: Optional[Mapping[str, Any]] = None,
        default_status (DefaultSensorStatus): Whether the sensor starts as running or not. The default
            status can be overridden from the Dagster UI or via the GraphQL API.
        minimum_interval_seconds (Optional[int]): The frequency at which to try to evaluate the
            sensor. The actual interval will be longer if the sensor evaluation takes longer than
            the provided interval.
        description (Optional[str]): A human-readable description of the sensor.
    """

    def __init__(
        self,
        name: str,
        *,
        asset_selection: CoercibleToAssetSelection,
        run_tags: Optional[Mapping[str, Any]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
    ):
        self._run_tags = normalize_tags(run_tags).tags

        super(DeclarativeSchedulingZone, self).__init__(
            name=check_valid_name(name),
            job_name=None,
            evaluation_fn=_ds_zone_implementation,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=None,
            jobs=None,
            default_status=default_status,
            required_resource_keys=None,
            asset_selection=asset_selection,
        )

    @property
    def run_tags(self) -> Mapping[str, str]:
        return self._run_tags

    @property
    def asset_selection(self) -> AssetSelection:
        return cast(AssetSelection, super().asset_selection)

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.DECLARATIVE_SCHEDULING_ZONE
