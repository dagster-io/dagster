from typing import Any, Mapping, Optional, cast

from dagster._annotations import experimental
from dagster._core.definitions.asset_selection import CoercibleToAssetSelection

from .asset_selection import AssetSelection
from .sensor_definition import DefaultSensorStatus, SensorDefinition, SensorType
from .utils import check_valid_name, validate_tags


@experimental
class AutomationPolicySensorDefinition(SensorDefinition):
    """Targets a set of assets and repeatedly evaluates all the AssetAutomationPolicys on all of
    those assets to determine which to request runs for.

    Args:
        name: The name of the sensor.
        asset_selection (Union[str, Sequence[str], Sequence[AssetKey], Sequence[Union[AssetsDefinition, SourceAsset]], AssetSelection]):
            The assets to evaluate AssetAutomationPolicys of and request runs for.
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
        self._run_tags = validate_tags(run_tags)

        def evaluation_fn(context):
            raise NotImplementedError(
                "Automation policy sensors cannot be evaluated like regular user-space sensors."
            )

        super(AutomationPolicySensorDefinition, self).__init__(
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
        return SensorType.AUTOMATION_POLICY
