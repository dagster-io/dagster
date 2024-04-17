import random
from abc import ABC, abstractmethod
from typing import Optional, Sequence

import dagster._check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.data_version import DATA_VERSION_TAG
from dagster._core.definitions.decorators.sensor_decorator import sensor
from dagster._core.definitions.events import AssetObservation
from dagster._core.definitions.run_request import SensorResult
from dagster._core.definitions.sensor_definition import SensorDefinition, SensorEvaluationContext
from dagster._model import DagsterModel


class ObserverEvaluationContext(DagsterModel):
    cursor: Optional[str]

    @staticmethod
    def from_sensor_evaluation_context(
        context: SensorEvaluationContext,
    ) -> "ObserverEvaluationContext":
        return ObserverEvaluationContext(cursor=context.cursor)


class ObserverEvaluationResult(DagsterModel):
    cursor: str
    updated: bool


class Observer(ABC):
    name: str
    observed_keys: Sequence[AssetKey]

    def __init__(
        self, name: Optional[str] = None, observed_keys: Optional[Sequence[AssetKey]] = None
    ):
        self.name = name or self.__class__.__name__
        self.observed_keys = observed_keys or [AssetKey(["_dagster_external", self.name])]

    @property
    def observed_key(self) -> AssetKey:
        check.invariant(len(self.observed_keys) == 1)
        return self.observed_keys[0]

    @abstractmethod
    def observe(self, context: ObserverEvaluationContext) -> ObserverEvaluationResult:
        pass

    def _get_sensor_result(self, observe_result: ObserverEvaluationResult) -> SensorResult:
        if observe_result.updated:
            return SensorResult(
                cursor=observe_result.cursor,
                asset_events=[
                    AssetObservation(
                        asset_key=self.observed_key,
                        tags={DATA_VERSION_TAG: str(random.randint(0, 100000000))},
                    )
                ],
            )
        else:
            return SensorResult(cursor=observe_result.cursor)

    def sensor(self) -> SensorDefinition:
        """Creates a SensorDefinition to periodically evaluate the observer."""

        @sensor(name=self.name)
        def _sensor(context: SensorEvaluationContext) -> SensorResult:
            observe_context = ObserverEvaluationContext.from_sensor_evaluation_context(context)
            observe_result = self.observe(observe_context)
            return self._get_sensor_result(observe_result)

        return _sensor
