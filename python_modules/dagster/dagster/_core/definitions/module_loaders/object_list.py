from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from functools import cached_property, reduce
from types import ModuleType
from typing import Any, Callable, Optional, Union, cast, get_args

from dagster._core.definitions.asset_checks.asset_checks_definition import (
    AssetChecksDefinition,
    has_only_asset_checks,
)
from dagster._core.definitions.asset_key import AssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.assets.definition.cacheable_assets_definition import (
    CacheableAssetsDefinition,
)
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.module_loaders.utils import (
    find_objects_in_module_of_types,
    key_iterator,
    replace_keys_in_asset,
)
from dagster._core.definitions.partitions.partitioned_schedule import (
    UnresolvedPartitionedAssetScheduleDefinition,
)
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.errors import DagsterInvalidDefinitionError

LoadableDagsterDef = Union[
    AssetsDefinition,
    SourceAsset,
    CacheableAssetsDefinition,
    AssetSpec,
    SensorDefinition,
    ScheduleDefinition,
    JobDefinition,
    UnresolvedAssetJobDefinition,
    UnresolvedPartitionedAssetScheduleDefinition,
]
ALL_LOADABLE_TYPES: tuple[type] = get_args(LoadableDagsterDef)


class ModuleScopedDagsterDefs:
    def __init__(self, objects_per_module: Mapping[str, Sequence[LoadableDagsterDef]]):
        self.objects_per_module = objects_per_module
        self._do_collision_detection()

    @classmethod
    def from_modules(
        cls,
        modules: Iterable[ModuleType],
        types_to_load: Optional[tuple[type]] = None,
    ) -> "ModuleScopedDagsterDefs":
        # Ensure that the types_to_load are all valid types.
        if types_to_load:
            for type_to_load in types_to_load:
                if type_to_load not in ALL_LOADABLE_TYPES:
                    raise DagsterInvalidDefinitionError(
                        f"Invalid type {type_to_load} provided in types_to_load. Must be one of {ALL_LOADABLE_TYPES}."
                    )
        return cls(
            {
                module.__name__: list(
                    find_objects_in_module_of_types(
                        module,
                        types_to_load or ALL_LOADABLE_TYPES,
                    )
                )
                for module in modules
            },
        )

    @cached_property
    def flat_object_list(self) -> Sequence[LoadableDagsterDef]:
        return [
            asset_object for objects in self.objects_per_module.values() for asset_object in objects
        ]

    @cached_property
    def objects_by_id(self) -> dict[int, LoadableDagsterDef]:
        return {id(asset_object): asset_object for asset_object in self.flat_object_list}

    @cached_property
    def deduped_objects(self) -> Sequence[LoadableDagsterDef]:
        return list(self.objects_by_id.values())

    @cached_property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return [asset for asset in self.deduped_objects if isinstance(asset, AssetsDefinition)]

    @cached_property
    def source_assets(self) -> Sequence[SourceAsset]:
        return [asset for asset in self.deduped_objects if isinstance(asset, SourceAsset)]

    @cached_property
    def schedule_defs(
        self,
    ) -> Sequence[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]:
        return [
            schedule
            for schedule in self.deduped_objects
            if isinstance(
                schedule, (ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition)
            )
        ]

    @cached_property
    def job_objects(self) -> Sequence[Union[JobDefinition, UnresolvedAssetJobDefinition]]:
        return [
            job
            for job in self.deduped_objects
            if isinstance(job, (JobDefinition, UnresolvedAssetJobDefinition))
        ]

    @cached_property
    def sensor_defs(self) -> Sequence[SensorDefinition]:
        return [sensor for sensor in self.deduped_objects if isinstance(sensor, SensorDefinition)]

    @cached_property
    def module_name_by_id(self) -> dict[int, str]:
        return {
            id(asset_object): module_name
            for module_name, objects in self.objects_per_module.items()
            for asset_object in objects
        }

    @cached_property
    def asset_objects_by_key(
        self,
    ) -> Mapping[AssetKey, Sequence[Union[SourceAsset, AssetSpec, AssetsDefinition]]]:
        objects_by_key = defaultdict(list)
        for asset_object in self.flat_object_list:
            if not isinstance(asset_object, (SourceAsset, AssetSpec, AssetsDefinition)):
                continue
            for key in key_iterator(asset_object):
                objects_by_key[key].append(asset_object)
        return objects_by_key

    def _do_collision_detection(self) -> None:
        # Collision detection on module-scoped asset objects. This does not include CacheableAssetsDefinitions, which don't have their keys defined until runtime.
        for key, asset_objects in self.asset_objects_by_key.items():
            # In certain cases, we allow asset specs to collide because we know we aren't loading them.
            # If there is more than one asset_object in the list for a given key, and the objects do not refer to the same asset_object in memory, we have a collision.

            # special handling for conflicting AssetSpecs since they are tuples and we can compare them with == and
            # dedupe at least those that dont contain nested complex objects
            if asset_objects and all(isinstance(obj, AssetSpec) for obj in asset_objects):
                first = asset_objects[0]
                num_distinct_objects_for_key = reduce(
                    lambda count, obj: count + int(obj != first),
                    asset_objects,
                    1,
                )
            else:
                num_distinct_objects_for_key = len(
                    set(id(asset_object) for asset_object in asset_objects)
                )
            if len(asset_objects) > 1 and num_distinct_objects_for_key > 1:
                asset_objects_str = ", ".join(
                    set(self.module_name_by_id[id(asset_object)] for asset_object in asset_objects)
                )
                raise DagsterInvalidDefinitionError(
                    f"Asset key {key.to_user_string()} is defined multiple times. Definitions found in modules: {asset_objects_str}."
                )
        # Collision detection on ScheduleDefinitions.
        schedule_defs_by_name = defaultdict(list)
        for schedule_def in self.schedule_defs:
            schedule_defs_by_name[schedule_def.name].append(schedule_def)
        for name, schedule_defs in schedule_defs_by_name.items():
            if len(schedule_defs) > 1:
                schedule_defs_str = ", ".join(
                    set(self.module_name_by_id[id(schedule_def)] for schedule_def in schedule_defs)
                )
                raise DagsterInvalidDefinitionError(
                    f"Schedule name {name} is defined multiple times. Definitions found in modules: {schedule_defs_str}."
                )

        # Collision detection on SensorDefinitions.
        sensor_defs_by_name = defaultdict(list)
        for sensor_def in self.sensor_defs:
            sensor_defs_by_name[sensor_def.name].append(sensor_def)
        for name, sensor_defs in sensor_defs_by_name.items():
            if len(sensor_defs) > 1:
                sensor_defs_str = ", ".join(
                    set(self.module_name_by_id[id(sensor_def)] for sensor_def in sensor_defs)
                )
                raise DagsterInvalidDefinitionError(
                    f"Sensor name {name} is defined multiple times. Definitions found in modules: {sensor_defs_str}."
                )

        # Collision detection on JobDefinitionObjects.
        job_objects_by_name = defaultdict(list)
        for job_object in self.job_objects:
            job_objects_by_name[job_object.name].append(job_object)
        for name, job_objects in job_objects_by_name.items():
            if len(job_objects) > 1:
                job_objects_str = ", ".join(
                    set(self.module_name_by_id[id(job_object)] for job_object in job_objects)
                )
                raise DagsterInvalidDefinitionError(
                    f"Job name {name} is defined multiple times. Definitions found in modules: {job_objects_str}."
                )

    def get_object_list(self) -> "DagsterObjectsList":
        return DagsterObjectsList(self.deduped_objects)


class DagsterObjectsList:
    def __init__(
        self,
        loaded_objects: Sequence[LoadableDagsterDef],
    ):
        self.loaded_defs = loaded_objects

    @cached_property
    def assets_defs_and_specs(self) -> Sequence[Union[AssetsDefinition, AssetSpec]]:
        return [
            asset
            for asset in self.loaded_defs
            if (isinstance(asset, AssetsDefinition) and asset.keys) or isinstance(asset, AssetSpec)
        ]

    @cached_property
    def assets_defs(self) -> Sequence[AssetsDefinition]:
        return [asset for asset in self.loaded_defs if isinstance(asset, AssetsDefinition)]

    @cached_property
    def checks_defs(self) -> Sequence[AssetChecksDefinition]:
        return [
            cast("AssetChecksDefinition", asset)
            for asset in self.loaded_defs
            if isinstance(asset, AssetsDefinition) and has_only_asset_checks(asset)
        ]

    @cached_property
    def assets_defs_specs_and_checks_defs(
        self,
    ) -> Sequence[Union[AssetsDefinition, AssetSpec, AssetChecksDefinition]]:
        return [*self.assets_defs_and_specs, *self.checks_defs]

    @cached_property
    def source_assets(self) -> Sequence[Union[SourceAsset, AssetSpec]]:
        return [
            dagster_def
            for dagster_def in self.loaded_defs
            if isinstance(dagster_def, (SourceAsset, AssetSpec))
        ]

    @cached_property
    def cacheable_assets(self) -> Sequence[CacheableAssetsDefinition]:
        return [
            dagster_def
            for dagster_def in self.loaded_defs
            if isinstance(dagster_def, CacheableAssetsDefinition)
        ]

    @cached_property
    def sensors(self) -> Sequence[SensorDefinition]:
        return [
            dagster_def
            for dagster_def in self.loaded_defs
            if isinstance(dagster_def, SensorDefinition)
        ]

    @cached_property
    def schedules(
        self,
    ) -> Sequence[Union[ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition]]:
        return [
            dagster_def
            for dagster_def in self.loaded_defs
            if isinstance(
                dagster_def, (ScheduleDefinition, UnresolvedPartitionedAssetScheduleDefinition)
            )
        ]

    @cached_property
    def jobs(self) -> Sequence[Union[JobDefinition, UnresolvedAssetJobDefinition]]:
        return [
            dagster_def
            for dagster_def in self.loaded_defs
            if isinstance(dagster_def, (JobDefinition, UnresolvedAssetJobDefinition))
        ]

    @cached_property
    def assets(
        self,
    ) -> Sequence[Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition, AssetSpec]]:
        return [
            *self.assets_defs_and_specs,
            *self.source_assets,
            *self.cacheable_assets,
        ]

    def get_objects(
        self, filter_fn: Callable[[LoadableDagsterDef], bool]
    ) -> Sequence[LoadableDagsterDef]:
        return [dagster_def for dagster_def in self.loaded_defs if filter_fn(dagster_def)]

    def assets_with_loadable_prefix(
        self, key_prefix: CoercibleToAssetKeyPrefix
    ) -> "DagsterObjectsList":
        # There is a tricky edge case here where if a non-cacheable asset depends on a cacheable asset,
        # and the assets are prefixed, the non-cacheable asset's dependency will not be prefixed since
        # at prefix-time it is not known that its dependency is one of the cacheable assets.
        # https://github.com/dagster-io/dagster/pull/10389#pullrequestreview-1170913271
        result_list = []
        all_asset_keys = {
            key
            for asset_object in self.assets_defs_specs_and_checks_defs
            for key in key_iterator(asset_object, included_targeted_keys=True)
        }
        key_replacements = {key: key.with_prefix(key_prefix) for key in all_asset_keys}
        for dagster_def in self.loaded_defs:
            if isinstance(dagster_def, CacheableAssetsDefinition):
                result_list.append(dagster_def.with_prefix_for_all(key_prefix))
            elif isinstance(dagster_def, AssetsDefinition):
                result_list.append(replace_keys_in_asset(dagster_def, key_replacements))
            else:
                # We don't replace the key for SourceAssets or AssetSpec objects (which can be thought of as the SourceAsset, or of course for non-asset objects.
                result_list.append(dagster_def)

        return DagsterObjectsList(result_list)

    def assets_with_source_prefix(
        self, key_prefix: CoercibleToAssetKeyPrefix
    ) -> "DagsterObjectsList":
        result_list = []
        key_replacements = {
            source_asset.key: source_asset.key.with_prefix(key_prefix)
            for source_asset in self.source_assets
        }
        for dagster_def in self.loaded_defs:
            if isinstance(
                dagster_def,
                (AssetSpec, SourceAsset, AssetsDefinition),
            ):
                result_list.append(replace_keys_in_asset(dagster_def, key_replacements))
            else:
                result_list.append(dagster_def)
        return DagsterObjectsList(result_list)

    def with_attributes(
        self,
        key_prefix: Optional[CoercibleToAssetKeyPrefix],
        source_key_prefix: Optional[CoercibleToAssetKeyPrefix],
        group_name: Optional[str],
        legacy_freshness_policy: Optional[LegacyFreshnessPolicy],
        automation_condition: Optional[AutomationCondition],
        backfill_policy: Optional[BackfillPolicy],
    ) -> "DagsterObjectsList":
        dagster_def_list = self.assets_with_loadable_prefix(key_prefix) if key_prefix else self
        dagster_def_list = (
            dagster_def_list.assets_with_source_prefix(source_key_prefix)
            if source_key_prefix
            else dagster_def_list
        )
        return_list = []
        for dagster_def in dagster_def_list.loaded_defs:
            if isinstance(dagster_def, AssetsDefinition):
                new_asset = dagster_def.map_asset_specs(
                    _spec_mapper_disallow_group_override(group_name, automation_condition)
                ).with_attributes(
                    backfill_policy=backfill_policy, legacy_freshness_policy=legacy_freshness_policy
                )
                return_list.append(
                    new_asset.coerce_to_checks_def()
                    if has_only_asset_checks(new_asset)
                    else new_asset
                )
            elif isinstance(dagster_def, SourceAsset):
                return_list.append(dagster_def.with_attributes(group_name=group_name))
            elif isinstance(dagster_def, AssetSpec):
                return_list.append(
                    _spec_mapper_disallow_group_override(group_name, automation_condition)(
                        dagster_def
                    )
                )
            elif isinstance(dagster_def, CacheableAssetsDefinition):
                return_list.append(
                    dagster_def.with_attributes_for_all(
                        group_name,
                        legacy_freshness_policy=legacy_freshness_policy,
                        auto_materialize_policy=automation_condition.as_auto_materialize_policy()
                        if automation_condition
                        else None,
                        backfill_policy=backfill_policy,
                    )
                )
            else:
                return_list.append(dagster_def)
        return DagsterObjectsList(return_list)

    def to_definitions_args(self) -> Mapping[str, Any]:
        return {
            "assets": self.assets,
            "asset_checks": self.checks_defs,
            "sensors": self.sensors,
            "schedules": self.schedules,
            "jobs": self.jobs,
        }


def _spec_mapper_disallow_group_override(
    group_name: Optional[str], automation_condition: Optional[AutomationCondition]
) -> Callable[[AssetSpec], AssetSpec]:
    def _inner(spec: AssetSpec) -> AssetSpec:
        if (
            group_name is not None
            and spec.group_name is not None
            and group_name != spec.group_name
            and spec.group_name != DEFAULT_GROUP_NAME
        ):
            raise DagsterInvalidDefinitionError(
                f"Asset spec {spec.key.to_user_string()} has group name {spec.group_name}, which conflicts with the group name {group_name} provided in load_assets_from_modules."
            )
        return spec.replace_attributes(
            group_name=group_name if group_name else ...,
            automation_condition=automation_condition if automation_condition else ...,
        )

    return _inner
