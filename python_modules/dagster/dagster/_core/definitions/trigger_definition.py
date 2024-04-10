import hashlib
import random
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Callable, Optional

from dagster._core.definitions.data_version import DataVersion
from dagster._core.definitions.result import ObserveResult
from dagster._core.definitions.run_request import RunRequest

if TYPE_CHECKING:
    from dagster._core.definitions.sensor_definition import (
        RawSensorEvaluationFunction,
        SensorDefinition,
        SensorEvaluationContext,
    )
from dagster._core.definitions.source_asset import SourceAsset

from .events import AssetKey


@dataclass
class TriggerResult:
    is_updated: bool
    cursor: Optional[str] = None


@dataclass
class TriggerDefinition:
    key: AssetKey
    # cron_schedule: str
    # would like this to be a cron schedule, but we need to build on top of the sensor system at
    # the moment in order to fire off runs for specific assets
    minimum_interval_seconds: int
    evaluation_fn: Callable[["SensorEvaluationContext"], TriggerResult]

    def _random_data_version(self) -> str:
        return hashlib.md5(str(random.random()).encode("utf-8")).hexdigest()[:24]

    def _get_sensor_evaluation_fn(self) -> "RawSensorEvaluationFunction":
        from dagster import SensorEvaluationContext, SensorResult

        def fn(context: SensorEvaluationContext) -> SensorResult:
            trigger_result = self.evaluation_fn(context)
            # request a run of the observe asset if the trigger is updated
            # TODO: maybe just directly yield an AssetObservation here
            run_requests = [RunRequest()] if trigger_result.is_updated else []
            return SensorResult(
                run_requests=run_requests,
                cursor=trigger_result.cursor,
            )

        return fn

    @cached_property
    def sensor(self) -> "SensorDefinition":
        from dagster import SensorDefinition

        return SensorDefinition(
            name=f"trigger__{self.key.to_python_identifier()}",
            minimum_interval_seconds=self.minimum_interval_seconds,
            evaluation_fn=self._get_sensor_evaluation_fn(),
            asset_selection=[self.key],
        )

    @cached_property
    def asset(self) -> SourceAsset:
        # whenever this asset is observed, it gets a new data version
        def _observe_fn() -> ObserveResult:
            return ObserveResult(
                asset_key=self.key,
                data_version=DataVersion(self._random_data_version()),
            )

        return SourceAsset(
            key=self.key,
            observe_fn=_observe_fn,
        )
