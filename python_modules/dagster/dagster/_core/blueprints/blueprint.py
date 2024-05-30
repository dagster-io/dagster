from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Mapping, NamedTuple, Optional, Union

from dagster import _check as check
from dagster._core.definitions.asset_checks import AssetChecksDefinition
from dagster._core.definitions.assets import AssetsDefinition, SourceAsset
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.executor_definition import ExecutorDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.logger_definition import LoggerDefinition
from dagster._core.definitions.partitioned_schedule import (
    UnresolvedPartitionedAssetScheduleDefinition,
)
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.executor.base import Executor
from dagster._model import DagsterModel
from dagster._utils.source_position import HasSourcePositionAndKeyPath


class DagsterBuildDefinitionsFromConfigError(Exception):
    pass


class BlueprintDefinitions(NamedTuple):
    """A bag of Dagster definitions.

    Unlike dagster.Definitions, BlueprintDefinitions does not do any validation at construction time
    on the set of definitions. For example, it can include assets without their required resources.
    """

    assets: Iterable[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]] = []
    schedules: Iterable[
        Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]
    ] = []
    sensors: Iterable[SensorDefinition] = []
    jobs: Iterable[Union[JobDefinition, UnresolvedAssetJobDefinition]] = []
    resources: Mapping[str, Any] = {}
    executor: Optional[Union[ExecutorDefinition, Executor]] = None
    loggers: Mapping[str, LoggerDefinition] = {}
    asset_checks: Iterable[AssetChecksDefinition] = []

    def to_definitions(self) -> Definitions:
        return Definitions(
            assets=self.assets,
            sensors=self.sensors,
            jobs=self.jobs,
            resources=self.resources,
            executor=self.executor,
            loggers=self.loggers,
            asset_checks=self.asset_checks,
        )

    @staticmethod
    def merge(*def_sets: "BlueprintDefinitions") -> "BlueprintDefinitions":
        """Merges multiple BlueprintDefinitions objects into a single BlueprintDefinitions object.

        The returned BlueprintDefinitions object has the union of all the definitions in the input
        BlueprintDefinitions objects.

        Returns:
            BlueprintDefinitions: The merged definitions.
        """
        assets = []
        schedules = []
        sensors = []
        jobs = []
        asset_checks = []

        resources = {}
        resource_key_indexes: Dict[str, int] = {}
        loggers = {}
        logger_key_indexes: Dict[str, int] = {}
        executor = None
        executor_index: Optional[int] = None

        for i, def_set in enumerate(def_sets):
            assets.extend(def_set.assets or [])
            asset_checks.extend(def_set.asset_checks or [])
            schedules.extend(def_set.schedules or [])
            sensors.extend(def_set.sensors or [])
            jobs.extend(def_set.jobs or [])

            for resource_key, resource_value in (def_set.resources or {}).items():
                if resource_key in resources:
                    raise DagsterInvariantViolationError(
                        f"Definitions objects {resource_key_indexes[resource_key]} and {i} both define a "
                        f"resource with key '{resource_key}'"
                    )
                resources[resource_key] = resource_value
                resource_key_indexes[resource_key] = i

            for logger_key, logger_value in (def_set.loggers or {}).items():
                if logger_key in loggers:
                    raise DagsterInvariantViolationError(
                        f"Definitions objects {logger_key_indexes[logger_key]} and {i} both define a "
                        f"logger with key '{logger_key}'"
                    )
                loggers[logger_key] = logger_value
                logger_key_indexes[logger_key] = i

            if def_set.executor is not None:
                if executor is not None and executor != def_set.executor:
                    raise DagsterInvariantViolationError(
                        f"Definitions objects {executor_index} and {i} both include an executor"
                    )

                executor = def_set.executor

        return BlueprintDefinitions(
            assets=assets,
            schedules=schedules,
            sensors=sensors,
            jobs=jobs,
            resources=resources,
            executor=executor,
            loggers=loggers,
            asset_checks=asset_checks,
        )


class Blueprint(DagsterModel, ABC, HasSourcePositionAndKeyPath):
    """A blob of user-provided, structured metadata that specifies a set of Dagster definitions,
    like assets, jobs, schedules, sensors, resources, or asset checks.

    Base class for user-provided types. Users override and provide:
    - The set of fields
    - A build_defs implementation that generates Dagster Definitions from field values
    """

    @abstractmethod
    def build_defs(self) -> BlueprintDefinitions:
        raise NotImplementedError()

    def build_defs_add_context_to_errors(self) -> BlueprintDefinitions:
        try:
            return check.inst(self.build_defs(), BlueprintDefinitions)
        except Exception as e:
            source_pos = None
            if (
                self._source_position_and_key_path is not None
                and self._source_position_and_key_path.source_position is not None
            ):
                source_pos = self._source_position_and_key_path.source_position

            cls_name = self.__class__.__name__
            if source_pos is None:
                raise DagsterBuildDefinitionsFromConfigError(
                    f"Error when building definitions from config with type {cls_name}"
                )
            raise DagsterBuildDefinitionsFromConfigError(
                f"Error when building definitions from config with type {cls_name} at {source_pos}"
            ) from e
