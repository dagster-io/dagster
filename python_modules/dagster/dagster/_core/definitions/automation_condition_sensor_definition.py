from functools import partial
from typing import Any, Mapping, Optional, cast

import dagster._check as check
from dagster._annotations import experimental
from dagster._core.definitions.asset_selection import AssetSelection, CoercibleToAssetSelection
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorEvaluationContext,
    SensorType,
)
from dagster._core.definitions.utils import check_valid_name
from dagster._utils.tags import normalize_tags


def _evaluate(sensor_def: "AutomationConditionSensorDefinition", context: SensorEvaluationContext):
    from dagster._core.definitions.automation_tick_evaluation_context import (
        AutomationTickEvaluationContext,
    )
    from dagster._daemon.asset_daemon import (
        asset_daemon_cursor_from_instigator_serialized_cursor,
        asset_daemon_cursor_to_instigator_serialized_cursor,
    )

    asset_graph = check.not_none(context.repository_def).asset_graph
    cursor = asset_daemon_cursor_from_instigator_serialized_cursor(
        context.cursor,
        asset_graph,
    )
    run_requests, new_cursor, updated_evaluations = AutomationTickEvaluationContext(
        evaluation_id=cursor.evaluation_id,
        instance=context.instance,
        asset_graph=asset_graph,
        cursor=cursor,
        materialize_run_tags=sensor_def.run_tags,
        observe_run_tags={},
        auto_observe_asset_keys=set(),
        asset_selection=sensor_def.asset_selection,
        allow_backfills=sensor_def.allow_backfills,
        default_condition=sensor_def.default_condition,
        logger=context.log,
    ).evaluate()

    return SensorResult(
        run_requests=run_requests,
        cursor=asset_daemon_cursor_to_instigator_serialized_cursor(new_cursor),
        automation_condition_evaluations=updated_evaluations,
    )


def not_supported(context) -> None:
    raise NotImplementedError(
        "Automation condition sensors cannot be evaluated like regular user-space sensors."
    )


@experimental
class AutomationConditionSensorDefinition(SensorDefinition):
    """Targets a set of assets and repeatedly evaluates all the AutomationConditions on all of
    those assets to determine which to request runs for.

    Args:
        name: The name of the sensor.
        asset_selection (Union[str, Sequence[str], Sequence[AssetKey], Sequence[Union[AssetsDefinition, SourceAsset]], AssetSelection]):
            The assets to evaluate AutomationConditions of and request runs for.
        tags (Optional[Mapping[str, str]]): A set of key-value tags that annotate the sensor and can
            be used for searching and filtering in the UI.
        run_tags (Optional[Mapping[str, Any]]): Tags that will be automatically attached to runs launched by this sensor.
        metadata (Optional[Mapping[str, object]]): A set of metadata entries that annotate the
            sensor. Values will be normalized to typed `MetadataValue` objects.
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
        tags: Optional[Mapping[str, str]] = None,
        run_tags: Optional[Mapping[str, Any]] = None,
        default_status: DefaultSensorStatus = DefaultSensorStatus.STOPPED,
        minimum_interval_seconds: Optional[int] = None,
        description: Optional[str] = None,
        metadata: Optional[Mapping[str, object]] = None,
        **kwargs,
    ):
        self._user_code = kwargs.get("user_code", False)
        self._allow_backfills = check.opt_bool_param(
            kwargs.get("allow_backfills"), "allow_backfills", default=False
        )
        check.param_invariant(
            not (self._allow_backfills and not self._user_code),
            "allow_backfills",
            "Setting `allow_backfills` for a non-user-code AutomationConditionSensorDefinition is not supported.",
        )
        self._default_condition = check.opt_inst_param(
            kwargs.get("default_condition"), "default_condition", AutomationCondition
        )
        check.param_invariant(
            not (self._default_condition and not self._user_code),
            "default_condition",
            "Setting a `default_condition` for a non-user-code AutomationConditionSensorDefinition is not supported.",
        )

        self._run_tags = normalize_tags(run_tags)

        super().__init__(
            name=check_valid_name(name),
            job_name=None,
            evaluation_fn=partial(_evaluate, self) if self._user_code else not_supported,
            minimum_interval_seconds=minimum_interval_seconds,
            description=description,
            job=None,
            jobs=None,
            default_status=default_status,
            required_resource_keys=None,
            asset_selection=asset_selection,
            tags=tags,
            metadata=metadata,
        )

    @property
    def run_tags(self) -> Mapping[str, str]:
        return self._run_tags

    @property
    def asset_selection(self) -> AssetSelection:
        return cast(AssetSelection, super().asset_selection)

    @property
    def allow_backfills(self) -> bool:
        return self._allow_backfills

    @property
    def default_condition(self) -> Optional[AutomationCondition]:
        return self._default_condition

    @property
    def sensor_type(self) -> SensorType:
        return SensorType.AUTOMATION if self._user_code else SensorType.AUTO_MATERIALIZE
