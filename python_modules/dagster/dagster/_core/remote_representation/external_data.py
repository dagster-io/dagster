"""This module contains data objects meant to be serialized between
host processes and user processes. They should contain no
business logic or clever indexing. Use the classes in external.py
for that.
"""

import json
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from typing import Any, Final, NamedTuple, Optional, Union, cast

from dagster_shared.serdes.serdes import (
    FieldSerializer,
    get_prefix_for_a_serialized,
    is_whitelisted_for_serdes_object,
)
from typing_extensions import Self, TypeAlias

from dagster import _check as check
from dagster._config.pythonic_config import (
    ConfigurableIOManagerFactoryResourceDefinition,
    ConfigurableResourceFactoryResourceDefinition,
)
from dagster._config.pythonic_config.resource import (
    coerce_to_resource,
    get_resource_type_name,
    is_coercible_to_resource,
)
from dagster._config.snap import ConfigFieldSnap, ConfigSchemaSnapshot, snap_from_config_type
from dagster._core.definitions import (
    AssetSelection,
    JobDefinition,
    PartitionsDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
)
from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_sensor_definition import AssetSensorDefinition
from dagster._core.definitions.assets.definition.asset_spec import AssetExecutionType
from dagster._core.definitions.assets.job.asset_job import is_reserved_asset_job_name
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition,
)
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.declarative_automation.serialized_objects import (
    AutomationConditionSnapshot,
)
from dagster._core.definitions.definition_config_schema import ConfiguredDefinitionConfigSchema
from dagster._core.definitions.dependency import (
    GraphNode,
    Node,
    NodeHandle,
    NodeOutputHandle,
    OpNode,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._core.definitions.freshness_policy import LegacyFreshnessPolicy
from dagster._core.definitions.metadata import (
    MetadataFieldSerializer,
    MetadataMapping,
    MetadataValue,
    TextMetadataValue,
    normalize_metadata,
)
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partitions.definition import (
    DynamicPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    TimeWindowPartitionsDefinition,
)
from dagster._core.definitions.partitions.mapping import PartitionMapping
from dagster._core.definitions.partitions.schedule_type import ScheduleType
from dagster._core.definitions.partitions.utils import get_builtin_partition_mapping_types
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.resource_requirement import ResourceKeyRequirement
from dagster._core.definitions.schedule_definition import DefaultScheduleStatus
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorType,
)
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.origin import RepositoryPythonOrigin
from dagster._core.snap import JobSnap
from dagster._core.snap.mode import ResourceDefSnap, build_resource_def_snap
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._core.storage.tags import COMPUTE_KIND_TAG, TAGS_INCLUDE_IN_REMOTE_JOB_REF
from dagster._core.utils import is_valid_email
from dagster._record import IHaveNew, record, record_custom
from dagster._serdes import whitelist_for_serdes
from dagster._time import datetime_from_timestamp
from dagster._utils.error import SerializableErrorInfo
from dagster._utils.warnings import suppress_dagster_warnings
from dagster.components.core.defs_module import (
    CompositeYamlComponent,
    DefsFolderComponent,
    PythonFileComponent,
)
from dagster.components.core.tree import ComponentTree

DEFAULT_MODE_NAME = "default"
DEFAULT_PRESET_NAME = "default"

# Historically, SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE could on the metadata of an asset
# to encode the execution type of the asset.
SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE = "dagster/asset_execution_type"


@whitelist_for_serdes(
    storage_name="ExternalRepositoryData",
    storage_field_names={
        "schedules": "external_schedule_datas",
        "partition_sets": "external_partition_set_datas",
        "sensors": "external_sensor_datas",
        "asset_nodes": "external_asset_graph_data",
        "resources": "external_resource_data",
        "asset_check_nodes": "external_asset_checks",
        "job_datas": "external_pipeline_datas",
        "job_refs": "external_job_refs",
    },
    skip_when_empty_fields={
        "pools",
        "component_tree",
    },
)
@record_custom
class RepositorySnap(IHaveNew):
    name: str
    schedules: Sequence["ScheduleSnap"]
    partition_sets: Sequence["PartitionSetSnap"]
    sensors: Sequence["SensorSnap"]
    asset_nodes: Sequence["AssetNodeSnap"]
    job_datas: Optional[Sequence["JobDataSnap"]]
    job_refs: Optional[Sequence["JobRefSnap"]]
    resources: Optional[Sequence["ResourceSnap"]]
    asset_check_nodes: Optional[Sequence["AssetCheckNodeSnap"]]
    metadata: Optional[MetadataMapping]
    utilized_env_vars: Optional[Mapping[str, Sequence["EnvVarConsumer"]]]
    component_tree: Optional["ComponentTreeSnap"]

    def __new__(
        cls,
        name: str,
        schedules: Sequence["ScheduleSnap"],
        partition_sets: Sequence["PartitionSetSnap"],
        sensors: Optional[Sequence["SensorSnap"]] = None,
        asset_nodes: Optional[Sequence["AssetNodeSnap"]] = None,
        job_datas: Optional[Sequence["JobDataSnap"]] = None,
        job_refs: Optional[Sequence["JobRefSnap"]] = None,
        resources: Optional[Sequence["ResourceSnap"]] = None,
        asset_check_nodes: Optional[Sequence["AssetCheckNodeSnap"]] = None,
        metadata: Optional[MetadataMapping] = None,
        utilized_env_vars: Optional[Mapping[str, Sequence["EnvVarConsumer"]]] = None,
        component_tree: Optional["ComponentTreeSnap"] = None,
    ):
        return super().__new__(
            cls,
            name=name,
            schedules=schedules,
            partition_sets=partition_sets,
            sensors=sensors or [],
            asset_nodes=asset_nodes or [],
            job_datas=job_datas,
            job_refs=job_refs,
            resources=resources,
            asset_check_nodes=asset_check_nodes,
            metadata=metadata or {},
            utilized_env_vars=utilized_env_vars,
            component_tree=component_tree,
        )

    @classmethod
    def from_def(
        cls,
        repository_def: RepositoryDefinition,
        defer_snapshots: bool = False,
    ) -> Self:
        check.inst_param(repository_def, "repository_def", RepositoryDefinition)

        jobs = repository_def.get_all_jobs()
        if defer_snapshots:
            job_datas = None
            job_refs = sorted(
                [JobRefSnap.from_job_def(job) for job in jobs],
                key=lambda pd: pd.name,
            )
        else:
            job_datas = sorted(
                list(
                    map(
                        lambda job: JobDataSnap.from_job_def(job, include_parent_snapshot=True),
                        jobs,
                    )
                ),
                key=lambda pd: pd.name,
            )
            job_refs = None

        resource_datas = repository_def.get_top_level_resources()
        asset_node_snaps = asset_node_snaps_from_repo(repository_def)

        nested_resource_map = _get_nested_resources_map(
            resource_datas, repository_def.get_top_level_resources()
        )
        inverted_nested_resources_map: dict[str, dict[str, str]] = defaultdict(dict)
        for resource_key, nested_resources in nested_resource_map.items():
            for attribute, nested_resource in nested_resources.items():
                if nested_resource.type == NestedResourceType.TOP_LEVEL:
                    inverted_nested_resources_map[nested_resource.name][resource_key] = attribute

        resource_asset_usage_map: dict[str, list[AssetKey]] = defaultdict(list)
        # collect resource usage from normal non-source assets
        for asset in asset_node_snaps:
            if asset.required_top_level_resources:
                for resource_key in asset.required_top_level_resources:
                    resource_asset_usage_map[resource_key].append(asset.asset_key)

        resource_schedule_usage_map: dict[str, list[str]] = defaultdict(list)
        for schedule in repository_def.schedule_defs:
            if schedule.required_resource_keys:
                for resource_key in schedule.required_resource_keys:
                    resource_schedule_usage_map[resource_key].append(schedule.name)

        resource_sensor_usage_map: dict[str, list[str]] = defaultdict(list)
        for sensor in repository_def.sensor_defs:
            if sensor.required_resource_keys:
                for resource_key in sensor.required_resource_keys:
                    resource_sensor_usage_map[resource_key].append(sensor.name)

        resource_job_usage_map: ResourceJobUsageMap = _get_resource_job_usage(jobs)

        component_snap = None
        component_tree = repository_def.get_component_tree()
        if component_tree:
            component_snap = ComponentTreeSnap.from_tree(component_tree)

        return cls(
            name=repository_def.name,
            schedules=sorted(
                [
                    ScheduleSnap.from_def(schedule_def, repository_def)
                    for schedule_def in repository_def.schedule_defs
                ],
                key=lambda sd: sd.name,
            ),
            # `PartitionSetDefinition` has been deleted, so we now construct `PartitionSetSnap`
            # from jobs instead of going through the intermediary `PartitionSetDefinition`. Eventually
            # we will remove `PartitionSetSnap` as well.
            partition_sets=sorted(
                [
                    PartitionSetSnap.from_job_def(job_def)
                    for job_def in repository_def.get_all_jobs()
                    if job_def.partitions_def is not None
                ],
                key=lambda pss: pss.name,
            ),
            sensors=sorted(
                [
                    SensorSnap.from_def(sensor_def, repository_def)
                    for sensor_def in repository_def.sensor_defs
                ],
                key=lambda sd: sd.name,
            ),
            asset_nodes=asset_node_snaps,
            job_datas=job_datas,
            job_refs=job_refs,
            resources=sorted(
                [
                    ResourceSnap.from_def(
                        res_data,
                        res_name,
                        nested_resource_map[res_name],
                        inverted_nested_resources_map[res_name],
                        resource_asset_usage_map,
                        resource_job_usage_map,
                        resource_schedule_usage_map,
                        resource_sensor_usage_map,
                    )
                    for res_name, res_data in resource_datas.items()
                ],
                key=lambda rd: rd.name,
            ),
            asset_check_nodes=asset_check_node_snaps_from_repo(repository_def),
            metadata=repository_def.metadata,
            utilized_env_vars={
                env_var: [
                    EnvVarConsumer(type=EnvVarConsumerType.RESOURCE, name=res_name)
                    for res_name in res_names
                ]
                for env_var, res_names in repository_def.get_env_vars_by_top_level_resource().items()
            },
            component_tree=component_snap,
        )

    def has_job_data(self):
        return self.job_datas is not None

    def get_job_datas(self) -> Sequence["JobDataSnap"]:
        if self.job_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")
        return self.job_datas

    def get_job_refs(self) -> Sequence["JobRefSnap"]:
        if self.job_refs is None:
            check.failed("Snapshots were not deferred, job_refs not loaded")
        return self.job_refs

    def get_job_snap(self, name):
        check.str_param(name, "name")
        if self.job_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")

        for job_data in self.job_datas:
            if job_data.name == name:
                return job_data.job

        check.failed("Could not find pipeline snapshot named " + name)

    def get_job_data(self, name):
        check.str_param(name, "name")
        if self.job_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")

        for job_data in self.job_datas:
            if job_data.name == name:
                return job_data

        check.failed("Could not find external pipeline data named " + name)

    def get_schedule(self, name):
        check.str_param(name, "name")

        for schedule in self.schedules:
            if schedule.name == name:
                return schedule

        check.failed("Could not find external schedule data named " + name)

    def has_partition_set(self, name) -> bool:
        check.str_param(name, "name")
        for partition_set in self.partition_sets:
            if partition_set.name == name:
                return True

        return False

    def get_partition_set(self, name) -> "PartitionSetSnap":
        check.str_param(name, "name")

        for partition_set in self.partition_sets:
            if partition_set.name == name:
                return partition_set

        check.failed("Could not find external partition set data named " + name)

    def get_sensor(self, name):
        check.str_param(name, "name")

        for sensor in self.sensors:
            if sensor.name == name:
                return sensor

        check.failed("Could not find sensor data named " + name)


@whitelist_for_serdes(
    storage_name="ExternalPresetData", storage_field_names={"op_selection": "solid_selection"}
)
@record_custom
class PresetSnap(IHaveNew):
    name: str
    run_config: Mapping[str, object]
    op_selection: Optional[Sequence[str]]
    mode: str
    tags: Mapping[str, str]

    def __new__(
        cls,
        name: str,
        run_config: Optional[Mapping[str, object]],
        op_selection: Optional[Sequence[str]],
        mode: str,
        tags: Optional[Mapping[str, str]],
    ):
        return super().__new__(
            cls,
            name=name,
            run_config=run_config or {},
            op_selection=op_selection,
            mode=mode,
            tags=tags or {},
        )


_JOB_SNAP_STORAGE_FIELD = "pipeline_snapshot"


@whitelist_for_serdes(
    storage_name="ExternalPipelineData",
    storage_field_names={
        "job": _JOB_SNAP_STORAGE_FIELD,
        "parent_job": "parent_pipeline_snapshot",
    },
    # There was a period during which `JobDefinition` was a newer subclass of the legacy
    # `PipelineDefinition`, and `is_job` was a boolean field used to distinguish between the two
    # cases on this class.
    old_fields={"is_job": True},
)
@record
class JobDataSnap:
    name: str
    job: JobSnap
    active_presets: Sequence["PresetSnap"]
    parent_job: Optional[JobSnap]

    @classmethod
    def from_job_def(cls, job_def: JobDefinition, include_parent_snapshot: bool) -> Self:
        return cls(
            name=job_def.name,
            job=job_def.get_job_snapshot(),
            parent_job=job_def.get_parent_job_snapshot() if include_parent_snapshot else None,
            active_presets=active_presets_from_job_def(job_def),
        )


@whitelist_for_serdes(
    storage_name="ExternalPipelineSubsetResult",
    storage_field_names={"job_data_snap": "external_pipeline_data"},
)
@record
class RemoteJobSubsetResult:
    success: bool
    error: Optional[SerializableErrorInfo] = None
    job_data_snap: Optional[JobDataSnap] = None
    repository_python_origin: Optional[RepositoryPythonOrigin] = None


@whitelist_for_serdes
class EnvVarConsumerType(Enum):
    RESOURCE = "RESOURCE"


@whitelist_for_serdes
class EnvVarConsumer(NamedTuple):
    type: EnvVarConsumerType
    name: str


@whitelist_for_serdes
class NestedResourceType(Enum):
    ANONYMOUS = "ANONYMOUS"
    TOP_LEVEL = "TOP_LEVEL"


@whitelist_for_serdes
class NestedResource(NamedTuple):
    type: NestedResourceType
    name: str


@whitelist_for_serdes(storage_name="ExternalJobRef", old_fields={"is_legacy_pipeline": False})
@record
class JobRefSnap:
    name: str
    snapshot_id: str
    active_presets: Sequence["PresetSnap"]
    parent_snapshot_id: Optional[str]
    preview_tags: Optional[Mapping[str, str]] = None

    @classmethod
    def from_job_def(cls, job_def: JobDefinition) -> Self:
        check.inst_param(job_def, "job_def", JobDefinition)

        return cls(
            name=job_def.name,
            snapshot_id=job_def.get_job_snapshot_id(),
            parent_snapshot_id=None,
            active_presets=active_presets_from_job_def(job_def),
            preview_tags=get_preview_tags(job_def),
        )

    def get_preview_tags(self) -> Mapping[str, str]:
        return self.preview_tags or {}


@whitelist_for_serdes(
    storage_name="ExternalScheduleData",
    storage_field_names={"job_name": "pipeline_name", "op_selection": "solid_selection"},
    skip_when_empty_fields={"default_status"},
)
@record_custom
class ScheduleSnap(IHaveNew):
    name: str
    cron_schedule: Union[str, Sequence[str]]
    job_name: str
    op_selection: Optional[Sequence[str]]
    mode: Optional[str]
    environment_vars: Mapping[str, str]
    partition_set_name: Optional[str]
    execution_timezone: Optional[str]
    description: Optional[str]
    default_status: Optional[DefaultScheduleStatus]
    asset_selection: Optional[AssetSelection]
    tags: Mapping[str, str]
    metadata: Mapping[str, MetadataValue]

    def __new__(
        cls,
        name: str,
        cron_schedule: Union[str, Sequence[str]],
        job_name: str,
        op_selection: Optional[Sequence[str]],
        mode: Optional[str],
        environment_vars: Optional[Mapping[str, str]],
        partition_set_name: Optional[str],
        execution_timezone: Optional[str],
        description: Optional[str] = None,
        default_status: Optional[DefaultScheduleStatus] = None,
        asset_selection: Optional[AssetSelection] = None,
        tags: Optional[Mapping[str, str]] = None,
        metadata: Optional[Mapping[str, MetadataValue]] = None,
    ):
        if asset_selection is not None:
            check.invariant(
                is_whitelisted_for_serdes_object(asset_selection),
                "asset_selection must be serializable",
            )

        return super().__new__(
            cls,
            name=name,
            cron_schedule=cron_schedule,
            job_name=job_name,
            op_selection=op_selection,
            mode=mode,
            environment_vars=environment_vars or {},
            partition_set_name=partition_set_name,
            execution_timezone=execution_timezone,
            description=description,
            # Leave default_status as None if it's STOPPED to maintain stable back-compat IDs
            default_status=(
                DefaultScheduleStatus.RUNNING
                if default_status == DefaultScheduleStatus.RUNNING
                else None
            ),
            asset_selection=asset_selection,
            tags=tags or {},
            metadata=metadata or {},
        )

    @classmethod
    def from_def(
        cls, schedule_def: ScheduleDefinition, repository_def: RepositoryDefinition
    ) -> Self:
        if schedule_def.has_anonymous_job:
            job_def = check.inst(
                schedule_def.job,
                UnresolvedAssetJobDefinition,
                "Anonymous job should be UnresolvedAssetJobDefinition",
            )
            serializable_asset_selection = job_def.selection.to_serializable_asset_selection(
                repository_def.asset_graph
            )
        else:
            serializable_asset_selection = None

        return cls(
            name=schedule_def.name,
            cron_schedule=schedule_def.cron_schedule,
            job_name=schedule_def.job_name,
            op_selection=schedule_def.target.op_selection,
            mode=DEFAULT_MODE_NAME,
            environment_vars=schedule_def.environment_vars,
            partition_set_name=None,
            execution_timezone=schedule_def.execution_timezone,
            description=schedule_def.description,
            default_status=schedule_def.default_status,
            asset_selection=serializable_asset_selection,
            tags=schedule_def.tags,
            metadata=schedule_def.metadata,
        )


@whitelist_for_serdes(storage_name="ExternalScheduleExecutionErrorData")
@record
class ScheduleExecutionErrorSnap:
    error: Optional[SerializableErrorInfo]


@whitelist_for_serdes(
    storage_name="ExternalTargetData",
    storage_field_names={"job_name": "pipeline_name", "op_selection": "solid_selection"},
)
@record
class TargetSnap:
    job_name: str
    mode: str
    op_selection: Optional[Sequence[str]]


@whitelist_for_serdes(storage_name="ExternalSensorMetadata")
@record
class SensorMetadataSnap:
    """Stores sensor metadata which is available in the Dagster UI.

    This is an unfortunate legacy class that is out of line with our preferred pattern of storing
    standard `Mapping[str, MetadataValue]` under the metadata field. Because this class already
    existed when adding this standard metadata to sensors, we stash it on here as a field under
    `standard_metadata`.
    """

    asset_keys: Optional[Sequence[AssetKey]]
    standard_metadata: Optional[Mapping[str, MetadataValue]] = None


@whitelist_for_serdes(
    storage_name="ExternalSensorData",
    storage_field_names={"job_name": "pipeline_name", "op_selection": "solid_selection"},
    skip_when_empty_fields={"default_status", "sensor_type"},
)
@record_custom
class SensorSnap(IHaveNew):
    name: str
    job_name: Optional[str]
    op_selection: Optional[Sequence[str]]
    mode: Optional[str]
    min_interval: Optional[int]
    description: Optional[str]
    target_dict: Mapping[str, TargetSnap]
    metadata: Optional[SensorMetadataSnap]
    default_status: Optional[DefaultSensorStatus]
    sensor_type: Optional[SensorType]
    asset_selection: Optional[AssetSelection]
    tags: Mapping[str, str]
    run_tags: Mapping[str, str]

    def __new__(
        cls,
        name: str,
        job_name: Optional[str] = None,
        op_selection: Optional[Sequence[str]] = None,
        mode: Optional[str] = None,
        min_interval: Optional[int] = None,
        description: Optional[str] = None,
        target_dict: Optional[Mapping[str, TargetSnap]] = None,
        metadata: Optional[SensorMetadataSnap] = None,
        default_status: Optional[DefaultSensorStatus] = None,
        sensor_type: Optional[SensorType] = None,
        asset_selection: Optional[AssetSelection] = None,
        tags: Optional[Mapping[str, str]] = None,
        run_tags: Optional[Mapping[str, str]] = None,
    ):
        if job_name and not target_dict:
            # handle the legacy case where the ExternalSensorData was constructed from an earlier
            # version of dagster
            target_dict = {
                job_name: TargetSnap(
                    job_name=check.str_param(job_name, "job_name"),
                    mode=check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME),
                    op_selection=check.opt_nullable_sequence_param(
                        op_selection, "op_selection", str
                    ),
                )
            }

        if asset_selection is not None:
            check.invariant(
                is_whitelisted_for_serdes_object(asset_selection),
                "asset_selection must be serializable",
            )

        return super().__new__(
            cls,
            name=name,
            job_name=job_name,  # keep legacy field populated
            op_selection=op_selection,  # keep legacy field populated
            mode=mode,  # keep legacy field populated
            min_interval=min_interval,
            description=description,
            target_dict=target_dict,
            metadata=metadata,
            # Leave default_status as None if it's STOPPED to maintain stable back-compat IDs
            default_status=(
                DefaultSensorStatus.RUNNING
                if default_status == DefaultSensorStatus.RUNNING
                else None
            ),
            sensor_type=sensor_type,
            asset_selection=asset_selection,
            tags=tags or {},
            run_tags=run_tags or {},
        )

    @classmethod
    def from_def(cls, sensor_def: SensorDefinition, repository_def: RepositoryDefinition) -> Self:
        first_target = sensor_def.targets[0] if sensor_def.targets else None

        asset_keys = None
        if isinstance(sensor_def, AssetSensorDefinition):
            asset_keys = [sensor_def.asset_key]

        if sensor_def.asset_selection is not None:
            target_dict = {
                base_asset_job_name: TargetSnap(
                    job_name=base_asset_job_name, mode=DEFAULT_MODE_NAME, op_selection=None
                )
                for base_asset_job_name in repository_def.get_implicit_asset_job_names()
            }

            serializable_asset_selection = (
                sensor_def.asset_selection.to_serializable_asset_selection(
                    repository_def.asset_graph
                )
            )
        else:
            target_dict = {
                target.job_name: TargetSnap(
                    job_name=target.job_name,
                    mode=DEFAULT_MODE_NAME,
                    op_selection=target.op_selection,
                )
                for target in sensor_def.targets
            }

            if sensor_def.has_anonymous_job:
                job_def = check.inst(
                    sensor_def.job,
                    UnresolvedAssetJobDefinition,
                    "Anonymous job should be UnresolvedAssetJobDefinition",
                )
                serializable_asset_selection = job_def.selection.to_serializable_asset_selection(
                    repository_def.asset_graph
                )
            else:
                serializable_asset_selection = None

        return cls(
            name=sensor_def.name,
            job_name=first_target.job_name if first_target else None,
            mode=None,
            op_selection=first_target.op_selection if first_target else None,
            target_dict=target_dict,
            min_interval=sensor_def.minimum_interval_seconds,
            description=sensor_def.description,
            metadata=SensorMetadataSnap(
                asset_keys=asset_keys, standard_metadata=sensor_def.metadata
            ),
            default_status=sensor_def.default_status,
            sensor_type=sensor_def.sensor_type,
            asset_selection=serializable_asset_selection,
            tags=sensor_def.tags,
            run_tags=(
                sensor_def.run_tags
                if isinstance(sensor_def, AutomationConditionSensorDefinition)
                else None
            ),
        )


@whitelist_for_serdes(storage_name="ExternalRepositoryErrorData")
@record
class RepositoryErrorSnap:
    error: Optional[SerializableErrorInfo]


@whitelist_for_serdes(storage_name="ExternalSensorExecutionErrorData")
@record
class SensorExecutionErrorSnap:
    error: Optional[SerializableErrorInfo]


@whitelist_for_serdes(storage_name="ExternalExecutionParamsData")
@record_custom
class ExecutionParamsSnap(IHaveNew):
    run_config: Mapping[str, object]
    tags: Mapping[str, str]

    def __new__(
        cls,
        run_config: Optional[Mapping[str, object]] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        return super().__new__(
            cls,
            run_config=run_config or {},
            tags=tags or {},
        )


@whitelist_for_serdes(storage_name="ExternalExecutionParamsErrorData")
@record
class ExecutionParamsErrorSnap:
    error: Optional[SerializableErrorInfo]


class PartitionsSnap(ABC):
    @classmethod
    def from_def(cls, partitions_def: PartitionsDefinition) -> "PartitionsSnap":
        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            return TimeWindowPartitionsSnap.from_def(partitions_def)
        elif isinstance(partitions_def, StaticPartitionsDefinition):
            return StaticPartitionsSnap.from_def(partitions_def)
        elif isinstance(partitions_def, MultiPartitionsDefinition):
            return MultiPartitionsSnap.from_def(partitions_def)
        elif isinstance(partitions_def, DynamicPartitionsDefinition):
            return DynamicPartitionsSnap.from_def(partitions_def)
        else:
            raise DagsterInvalidDefinitionError(
                "Only static, time window, multi-dimensional partitions, and dynamic partitions"
                " definitions with a name parameter are currently supported."
            )

    @abstractmethod
    def get_partitions_definition(self) -> PartitionsDefinition: ...


@whitelist_for_serdes(storage_name="ExternalTimeWindowPartitionsDefinitionData")
@record
class TimeWindowPartitionsSnap(PartitionsSnap):
    start: float
    timezone: Optional[str]
    fmt: str
    end_offset: int
    end: Optional[float] = None
    cron_schedule: Optional[str] = None
    # superseded by cron_schedule, but kept around for backcompat
    schedule_type: Optional[ScheduleType] = None
    # superseded by cron_schedule, but kept around for backcompat
    minute_offset: Optional[int] = None
    # superseded by cron_schedule, but kept around for backcompat
    hour_offset: Optional[int] = None
    # superseded by cron_schedule, but kept around for backcompat
    day_offset: Optional[int] = None

    @classmethod
    def from_def(cls, partitions_def: TimeWindowPartitionsDefinition) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        check.inst_param(partitions_def, "partitions_def", TimeWindowPartitionsDefinition)
        return cls(
            cron_schedule=partitions_def.cron_schedule,
            start=partitions_def.start.timestamp(),
            end=partitions_def.end.timestamp() if partitions_def.end else None,
            timezone=partitions_def.timezone,
            fmt=partitions_def.fmt,
            end_offset=partitions_def.end_offset,
        )

    def get_partitions_definition(self):
        if self.cron_schedule is not None:
            return TimeWindowPartitionsDefinition(
                cron_schedule=self.cron_schedule,
                start=datetime_from_timestamp(self.start, tz=self.timezone),  # pyright: ignore[reportArgumentType]
                timezone=self.timezone,
                fmt=self.fmt,
                end_offset=self.end_offset,
                end=(datetime_from_timestamp(self.end, tz=self.timezone) if self.end else None),  # pyright: ignore[reportArgumentType]
            )
        else:
            # backcompat case
            return TimeWindowPartitionsDefinition(
                schedule_type=self.schedule_type,
                start=datetime_from_timestamp(self.start, tz=self.timezone),  # pyright: ignore[reportArgumentType]
                timezone=self.timezone,
                fmt=self.fmt,
                end_offset=self.end_offset,
                end=(datetime_from_timestamp(self.end, tz=self.timezone) if self.end else None),  # pyright: ignore[reportArgumentType]
                minute_offset=self.minute_offset,
                hour_offset=self.hour_offset,
                day_offset=self.day_offset,
            )


def _dedup_partition_keys(keys: Sequence[str]) -> Sequence[str]:
    # Use both a set and a list here to preserve lookup performance in case of large inputs. (We
    # can't just use a set because we need to preserve ordering.)
    seen_keys: set[str] = set()
    new_keys: list[str] = []
    for key in keys:
        if key not in seen_keys:
            new_keys.append(key)
            seen_keys.add(key)
    return new_keys


@whitelist_for_serdes(storage_name="ExternalStaticPartitionsDefinitionData")
@record_custom(checked=False)
class StaticPartitionsSnap(PartitionsSnap, IHaveNew):
    partition_keys: Sequence[str]

    def __new__(cls, partition_keys: Sequence[str]):
        # for back compat reasons we allow str as a Sequence[str] here
        if not isinstance(partition_keys, str):
            check.sequence_param(
                partition_keys,
                "partition_keys",
                of_type=str,
            )

        return super().__new__(
            cls,
            partition_keys=partition_keys,
        )

    @classmethod
    def from_def(cls, partitions_def: StaticPartitionsDefinition) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        check.inst_param(partitions_def, "partitions_def", StaticPartitionsDefinition)
        return cls(partition_keys=partitions_def.get_partition_keys())

    def get_partitions_definition(self):
        # v1.4 made `StaticPartitionsDefinition` error if given duplicate keys. This caused
        # host process errors for users who had not upgraded their user code to 1.4 and had dup
        # keys, since the host process `StaticPartitionsDefinition` would throw an error.
        keys = _dedup_partition_keys(self.partition_keys)
        return StaticPartitionsDefinition(keys)


@whitelist_for_serdes(
    storage_name="ExternalPartitionDimensionDefinition",
    storage_field_names={"partitions": "external_partitions_def_data"},
)
@record
class PartitionDimensionSnap:
    name: str
    partitions: PartitionsSnap


@whitelist_for_serdes(
    storage_name="ExternalMultiPartitionsDefinitionData",
    storage_field_names={"partition_dimensions": "external_partition_dimension_definitions"},
)
@record
class MultiPartitionsSnap(PartitionsSnap):
    partition_dimensions: Sequence[PartitionDimensionSnap]

    @classmethod
    def from_def(cls, partitions_def: MultiPartitionsDefinition) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        check.inst_param(partitions_def, "partitions_def", MultiPartitionsDefinition)

        return cls(
            partition_dimensions=[
                PartitionDimensionSnap(
                    name=dimension.name,
                    partitions=PartitionsSnap.from_def(dimension.partitions_def),
                )
                for dimension in partitions_def.partitions_defs
            ]
        )

    def get_partitions_definition(self):
        return MultiPartitionsDefinition(
            {
                partition_dimension.name: (
                    partition_dimension.partitions.get_partitions_definition()
                )
                for partition_dimension in self.partition_dimensions
            }
        )


@whitelist_for_serdes(storage_name="ExternalDynamicPartitionsDefinitionData")
@record
class DynamicPartitionsSnap(PartitionsSnap):
    name: str

    @classmethod
    def from_def(cls, partitions_def: DynamicPartitionsDefinition) -> Self:  # pyright: ignore[reportIncompatibleMethodOverride]
        check.inst_param(partitions_def, "partitions_def", DynamicPartitionsDefinition)
        if partitions_def.name is None:
            raise DagsterInvalidDefinitionError(
                "Dagster does not support dynamic partitions definitions without a name parameter."
            )
        return cls(name=partitions_def.name)

    def get_partitions_definition(self):
        return DynamicPartitionsDefinition(name=self.name)


@whitelist_for_serdes(
    storage_name="ExternalPartitionSetData",
    storage_field_names={
        "job_name": "pipeline_name",
        "op_selection": "solid_selection",
        "partitions": "external_partitions_data",
    },
)
@record
class PartitionSetSnap:
    name: str
    job_name: str
    op_selection: Optional[Sequence[str]]
    mode: Optional[str]
    partitions: Optional[PartitionsSnap] = None
    backfill_policy: Optional[BackfillPolicy] = None

    @classmethod
    def from_job_def(cls, job_def: JobDefinition) -> Self:
        check.inst_param(job_def, "job_def", JobDefinition)
        partitions_def = check.not_none(job_def.partitions_def)

        partitions_snap: Optional[PartitionsSnap] = None
        if isinstance(partitions_def, TimeWindowPartitionsDefinition):
            partitions_snap = TimeWindowPartitionsSnap.from_def(partitions_def)
        elif isinstance(partitions_def, StaticPartitionsDefinition):
            partitions_snap = StaticPartitionsSnap.from_def(partitions_def)
        elif (
            isinstance(partitions_def, DynamicPartitionsDefinition)
            and partitions_def.name is not None
        ):
            partitions_snap = DynamicPartitionsSnap.from_def(partitions_def)
        elif isinstance(partitions_def, MultiPartitionsDefinition):
            partitions_snap = MultiPartitionsSnap.from_def(partitions_def)
        else:
            partitions_snap = None

        return cls(
            name=partition_set_snap_name_for_job_name(job_def.name),
            job_name=job_def.name,
            op_selection=None,
            mode=DEFAULT_MODE_NAME,
            partitions=partitions_snap,
            backfill_policy=job_def.backfill_policy,
        )


@whitelist_for_serdes(storage_name="ExternalPartitionNamesData")
@record_custom
class PartitionNamesSnap(IHaveNew):
    partition_names: Sequence[str]

    def __new__(cls, partition_names: Optional[Sequence[str]] = None):
        return super().__new__(
            cls,
            partition_names=partition_names or [],
        )


@whitelist_for_serdes(storage_name="ExternalPartitionConfigData")
@record_custom
class PartitionConfigSnap(IHaveNew):
    name: str
    run_config: Mapping[str, object]

    def __new__(cls, name: str, run_config: Optional[Mapping[str, object]] = None):
        return super().__new__(
            cls,
            name=name,
            run_config=run_config or {},
        )


@whitelist_for_serdes(storage_name="ExternalPartitionTagsData")
@record_custom
class PartitionTagsSnap(IHaveNew):
    name: str
    tags: Mapping[str, object]

    def __new__(cls, name: str, tags: Optional[Mapping[str, str]] = None):
        return super().__new__(
            cls,
            name=name,
            tags=tags or {},
        )


@whitelist_for_serdes(storage_name="ExternalPartitionExecutionParamData")
@record
class PartitionExecutionParamSnap:
    name: str
    tags: Mapping[str, str]
    run_config: Mapping[str, object]


@whitelist_for_serdes(storage_name="ExternalPartitionSetExecutionParamData")
@record
class PartitionSetExecutionParamSnap:
    partition_data: Sequence[PartitionExecutionParamSnap]


@whitelist_for_serdes(storage_name="ExternalPartitionExecutionErrorData")
@record
class PartitionExecutionErrorSnap:
    error: Optional[SerializableErrorInfo]


@whitelist_for_serdes(
    storage_name="ExternalAssetDependency",
    storage_field_names={"parent_asset_key": "upstream_asset_key"},
)
@record
class AssetParentEdgeSnap:
    """A definition of a directed edge in the logical asset graph.

    An upstream asset that's depended on, and the corresponding input name in the downstream asset
    that depends on it.
    """

    parent_asset_key: AssetKey
    input_name: Optional[str] = None
    output_name: Optional[str] = None
    partition_mapping: Optional[PartitionMapping] = None


@whitelist_for_serdes(
    storage_name="ExternalAssetDependedBy",
    storage_field_names={"child_asset_key": "downstream_asset_key"},
)
@record
class AssetChildEdgeSnap:
    """A definition of a directed edge in the logical asset graph.

    An downstream asset that's depended by, and the corresponding input name in the upstream
    asset that it depends on.
    """

    child_asset_key: AssetKey
    input_name: Optional[str] = None
    output_name: Optional[str] = None


@whitelist_for_serdes(storage_name="ExternalResourceConfigEnvVar")
@record
class ResourceConfigEnvVarSnap:
    name: str


ResourceValueSnap: TypeAlias = Union[str, ResourceConfigEnvVarSnap]


UNKNOWN_RESOURCE_TYPE = "Unknown"


@whitelist_for_serdes
@record
class ResourceJobUsageEntry:
    """Stores information about where a resource is used in a job."""

    job_name: str
    node_handles: list[NodeHandle]


@whitelist_for_serdes(storage_name="ExternalResourceData")
@record_custom
class ResourceSnap(IHaveNew):
    """Serializable data associated with a top-level resource in a Repository, e.g. one bound using the Definitions API.

    Includes information about the resource definition and config schema, user-passed values, etc.
    """

    name: str
    resource_snapshot: ResourceDefSnap
    configured_values: dict[str, ResourceValueSnap]
    config_field_snaps: list[ConfigFieldSnap]
    config_schema_snap: ConfigSchemaSnapshot
    nested_resources: dict[str, NestedResource]
    parent_resources: dict[str, str]
    resource_type: str
    is_top_level: bool
    asset_keys_using: list[AssetKey]
    job_ops_using: list[ResourceJobUsageEntry]
    dagster_maintained: bool
    schedules_using: list[str]
    sensors_using: list[str]

    def __new__(
        cls,
        name: str,
        resource_snapshot: ResourceDefSnap,
        configured_values: Mapping[str, ResourceValueSnap],
        config_field_snaps: Sequence[ConfigFieldSnap],
        config_schema_snap: ConfigSchemaSnapshot,
        nested_resources: Optional[Mapping[str, NestedResource]] = None,
        parent_resources: Optional[Mapping[str, str]] = None,
        resource_type: str = UNKNOWN_RESOURCE_TYPE,
        is_top_level: bool = True,
        asset_keys_using: Optional[Sequence[AssetKey]] = None,
        job_ops_using: Optional[Sequence[ResourceJobUsageEntry]] = None,
        dagster_maintained: bool = False,
        schedules_using: Optional[Sequence[str]] = None,
        sensors_using: Optional[Sequence[str]] = None,
    ):
        return super().__new__(
            cls,
            name=name,
            resource_snapshot=resource_snapshot,
            configured_values=dict(
                check.mapping_param(
                    configured_values,
                    "configured_values",
                    key_type=str,
                    value_type=(str, ResourceConfigEnvVarSnap),
                )
            ),
            config_field_snaps=config_field_snaps,
            config_schema_snap=config_schema_snap,
            nested_resources=dict(
                check.opt_mapping_param(
                    nested_resources, "nested_resources", key_type=str, value_type=NestedResource
                )
            ),
            parent_resources=dict(
                check.opt_mapping_param(
                    parent_resources, "parent_resources", key_type=str, value_type=str
                )
            ),
            is_top_level=is_top_level,
            resource_type=resource_type,
            asset_keys_using=list(
                check.opt_sequence_param(asset_keys_using, "asset_keys_using", of_type=AssetKey)
            ),
            job_ops_using=list(
                check.opt_sequence_param(
                    job_ops_using, "job_ops_using", of_type=ResourceJobUsageEntry
                )
            ),
            dagster_maintained=dagster_maintained,
            schedules_using=list(
                check.opt_sequence_param(schedules_using, "schedules_using", of_type=str)
            ),
            sensors_using=list(
                check.opt_sequence_param(sensors_using, "sensors_using", of_type=str)
            ),
        )

    @classmethod
    def from_def(
        cls,
        resource_def: ResourceDefinition,
        name: str,
        nested_resources: Mapping[str, NestedResource],
        parent_resources: Mapping[str, str],
        resource_asset_usage_map: Mapping[str, list[AssetKey]],
        resource_job_usage_map: "ResourceJobUsageMap",
        resource_schedule_usage_map: Mapping[str, list[str]],
        resource_sensor_usage_map: Mapping[str, list[str]],
    ) -> Self:
        check.inst_param(resource_def, "resource_def", ResourceDefinition)

        # Once values on a resource object are bound, the config schema for those fields is no
        # longer visible. We walk up the list of parent schemas to find the base, unconfigured
        # schema so we can display all fields in the UI.
        unconfigured_config_schema = resource_def.config_schema
        while (
            isinstance(unconfigured_config_schema, ConfiguredDefinitionConfigSchema)
            and unconfigured_config_schema.parent_def.config_schema
        ):
            unconfigured_config_schema = unconfigured_config_schema.parent_def.config_schema

        config_type = check.not_none(unconfigured_config_schema.config_type)
        unconfigured_config_type_snap = snap_from_config_type(config_type)

        config_schema_default = cast(
            "Mapping[str, Any]",
            (
                json.loads(resource_def.config_schema.default_value_as_json_str)
                if resource_def.config_schema.default_provided
                else {}
            ),
        )

        # Right now, .configured sets the default value of the top-level Field
        # we parse the JSON and break it out into defaults for each individual nested Field
        # for display in the UI
        configured_values = {
            k: resource_value_snap_from_raw(v) for k, v in config_schema_default.items()
        }

        resource_type_def = resource_def
        resource_type = get_resource_type_name(resource_type_def)

        dagster_maintained = (
            resource_type_def._is_dagster_maintained()  # noqa: SLF001
            if type(resource_type_def)
            in (
                ResourceDefinition,
                IOManagerDefinition,
                ConfigurableResourceFactoryResourceDefinition,
                ConfigurableIOManagerFactoryResourceDefinition,
            )
            else False
        )

        return cls(
            name=name,
            resource_snapshot=build_resource_def_snap(name, resource_def),
            configured_values=configured_values,
            config_field_snaps=unconfigured_config_type_snap.fields or [],
            config_schema_snap=config_type.schema_snapshot,
            nested_resources=nested_resources,
            parent_resources=parent_resources,
            is_top_level=True,
            asset_keys_using=resource_asset_usage_map.get(name, []),
            job_ops_using=resource_job_usage_map.get(name, []),
            schedules_using=resource_schedule_usage_map.get(name, []),
            sensors_using=resource_sensor_usage_map.get(name, []),
            resource_type=resource_type,
            dagster_maintained=dagster_maintained,
        )


@whitelist_for_serdes(
    storage_name="ExternalAssetCheck",
    storage_field_names={"execution_set_identifier": "atomic_execution_unit_id"},
)
@record_custom
class AssetCheckNodeSnap(IHaveNew):
    """Serializable data associated with an asset check."""

    name: str
    asset_key: AssetKey
    description: Optional[str]
    execution_set_identifier: Optional[str]
    job_names: Sequence[str]
    blocking: bool
    additional_asset_keys: Sequence[AssetKey]
    automation_condition: Optional[AutomationCondition]
    automation_condition_snapshot: Optional[AutomationConditionSnapshot]

    def __new__(
        cls,
        name: str,
        asset_key: AssetKey,
        description: Optional[str],
        execution_set_identifier: Optional[str] = None,
        job_names: Optional[Sequence[str]] = None,
        blocking: bool = False,
        additional_asset_keys: Optional[Sequence[AssetKey]] = None,
        automation_condition: Optional[AutomationCondition] = None,
        automation_condition_snapshot: Optional[AutomationConditionSnapshot] = None,
    ):
        return super().__new__(
            cls,
            name=name,
            asset_key=asset_key,
            description=description,
            execution_set_identifier=execution_set_identifier,
            job_names=job_names or [],
            blocking=blocking,
            additional_asset_keys=additional_asset_keys or [],
            automation_condition=automation_condition,
            automation_condition_snapshot=automation_condition_snapshot,
        )

    @property
    def key(self) -> AssetCheckKey:
        return AssetCheckKey(asset_key=self.asset_key, name=self.name)


class BackcompatTeamOwnerFieldDeserializer(FieldSerializer):
    """Up through Dagster 1.7.7, asset owners provided as "team:foo" would be serialized as "foo"
    going forward, they're serialized as "team:foo".
    """

    def unpack(self, __unpacked_value, whitelist_map, context):
        return (
            [
                owner if (is_valid_email(owner) or owner.startswith("team:")) else f"team:{owner}"
                for owner in cast("Sequence[str]", __unpacked_value)
            ]
            if __unpacked_value is not None
            else None
        )

    def pack(self, __unpacked_value, whitelist_map, descent_path):
        return __unpacked_value


@whitelist_for_serdes(
    storage_name="ExternalAssetNode",
    storage_field_names={
        "child_edges": "depended_by",
        "parent_edges": "dependencies",
        "metadata": "metadata_entries",
        "execution_set_identifier": "atomic_execution_unit_id",
        "description": "op_description",
        "partitions": "partitions_def_data",
        "legacy_freshness_policy": "freshness_policy",
        "freshness_policy": "new_freshness_policy",
    },
    field_serializers={
        "metadata": MetadataFieldSerializer,
        "owners": BackcompatTeamOwnerFieldDeserializer,
    },
)
@suppress_dagster_warnings
@record_custom
class AssetNodeSnap(IHaveNew):
    """A definition of a node in the logical asset graph.

    A function for computing the asset and an identifier for that asset.
    """

    asset_key: AssetKey
    parent_edges: Sequence[AssetParentEdgeSnap]
    child_edges: Sequence[AssetChildEdgeSnap]
    execution_type: AssetExecutionType
    pools: set[str]
    compute_kind: Optional[str]
    op_name: Optional[str]
    op_names: Sequence[str]
    code_version: Optional[str]
    node_definition_name: Optional[str]
    graph_name: Optional[str]
    description: Optional[str]
    job_names: Sequence[str]
    partitions: Optional[PartitionsSnap]
    output_name: Optional[str]
    metadata: Mapping[str, MetadataValue]
    tags: Optional[Mapping[str, str]]
    group_name: str
    legacy_freshness_policy: Optional[LegacyFreshnessPolicy]
    freshness_policy: Optional[InternalFreshnessPolicy]
    is_source: bool
    is_observable: bool
    # If a set of assets can't be materialized independently from each other, they will all
    # have the same execution_set_identifier. This ID should be stable across reloads and
    # unique deployment-wide.
    execution_set_identifier: Optional[str]
    required_top_level_resources: Optional[Sequence[str]]
    auto_materialize_policy: Optional[AutoMaterializePolicy]
    automation_condition_snapshot: Optional[AutomationConditionSnapshot]
    backfill_policy: Optional[BackfillPolicy]
    auto_observe_interval_minutes: Optional[Union[float, int]]
    owners: Optional[Sequence[str]]

    def __new__(
        cls,
        asset_key: AssetKey,
        parent_edges: Sequence[AssetParentEdgeSnap],
        child_edges: Sequence[AssetChildEdgeSnap],
        execution_type: Optional[AssetExecutionType] = None,
        pools: Optional[set[str]] = None,
        compute_kind: Optional[str] = None,
        op_name: Optional[str] = None,
        op_names: Optional[Sequence[str]] = None,
        code_version: Optional[str] = None,
        node_definition_name: Optional[str] = None,
        graph_name: Optional[str] = None,
        description: Optional[str] = None,
        job_names: Optional[Sequence[str]] = None,
        partitions: Optional[PartitionsSnap] = None,
        output_name: Optional[str] = None,
        metadata: Optional[Mapping[str, MetadataValue]] = None,
        tags: Optional[Mapping[str, str]] = None,
        group_name: Optional[str] = None,
        legacy_freshness_policy: Optional[LegacyFreshnessPolicy] = None,
        freshness_policy: Optional[InternalFreshnessPolicy] = None,
        is_source: Optional[bool] = None,
        is_observable: bool = False,
        execution_set_identifier: Optional[str] = None,
        required_top_level_resources: Optional[Sequence[str]] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
        automation_condition_snapshot: Optional[AutomationConditionSnapshot] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        auto_observe_interval_minutes: Optional[Union[float, int]] = None,
        owners: Optional[Sequence[str]] = None,
    ):
        metadata = normalize_metadata(
            check.opt_mapping_param(metadata, "metadata", key_type=str), allow_invalid=True
        )

        # backcompat logic for execution type specified via metadata
        if SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE in metadata:
            val = metadata[SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE]
            if not isinstance(val, TextMetadataValue):
                check.failed(
                    f"Expected metadata value for key {SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE} to be a TextMetadataValue, got {val}"
                )
            metadata_execution_type = AssetExecutionType[check.not_none(val.value)]
            if execution_type is not None:
                check.invariant(
                    execution_type == metadata_execution_type,
                    f"Execution type {execution_type} in metadata does not match type inferred from metadata {metadata_execution_type}",
                )
            execution_type = metadata_execution_type
        else:
            if is_source and is_observable:
                default_execution_type = AssetExecutionType.OBSERVATION
            elif is_source:
                default_execution_type = AssetExecutionType.UNEXECUTABLE
            else:
                default_execution_type = AssetExecutionType.MATERIALIZATION

            execution_type = (
                check.opt_inst_param(
                    execution_type,
                    "execution_type",
                    AssetExecutionType,
                )
                or default_execution_type
            )

        # backcompat logic to handle AssetNodeSnaps serialized without op_names/graph_name
        if not op_names:
            op_names = list(filter(None, [op_name]))

        # backcompat logic to handle AssetNodeSnaps serialzied without is_source
        if is_source is None:
            # prior to this field being added, all non-source assets must be part of at least one
            # job, and no source assets could be part of any job
            is_source = len(job_names or []) == 0

        return super().__new__(
            cls,
            asset_key=asset_key,
            parent_edges=parent_edges or [],
            child_edges=child_edges or [],
            compute_kind=compute_kind,
            pools=pools or set(),
            op_name=op_name,
            op_names=op_names or [],
            code_version=code_version,
            node_definition_name=node_definition_name,
            graph_name=graph_name,
            description=description,
            job_names=job_names or [],
            partitions=partitions,
            output_name=output_name,
            metadata=metadata,
            tags=tags or {},
            # Newer code always passes a string group name when constructing these, but we assign
            # the default here for backcompat.
            group_name=group_name or DEFAULT_GROUP_NAME,
            legacy_freshness_policy=legacy_freshness_policy,
            freshness_policy=freshness_policy
            or InternalFreshnessPolicy.from_asset_spec_metadata(metadata),
            is_source=is_source,
            is_observable=is_observable,
            execution_set_identifier=execution_set_identifier,
            required_top_level_resources=required_top_level_resources or [],
            auto_materialize_policy=auto_materialize_policy,
            automation_condition_snapshot=automation_condition_snapshot,
            backfill_policy=backfill_policy,
            auto_observe_interval_minutes=auto_observe_interval_minutes,
            owners=owners or [],
            execution_type=execution_type,
        )

    @property
    def is_materializable(self) -> bool:
        return self.execution_type == AssetExecutionType.MATERIALIZATION

    @property
    def is_external(self) -> bool:
        return self.execution_type != AssetExecutionType.MATERIALIZATION

    @property
    def is_executable(self) -> bool:
        return self.execution_type != AssetExecutionType.UNEXECUTABLE

    @property
    def automation_condition(self) -> Optional[AutomationCondition]:
        if self.auto_materialize_policy is not None:
            return self.auto_materialize_policy.to_automation_condition()
        else:
            return None


ResourceJobUsageMap: TypeAlias = dict[str, list[ResourceJobUsageEntry]]


class NodeHandleResourceUse(NamedTuple):
    resource_key: str
    node_handle: NodeHandle


def _get_resource_usage_from_node(
    pipeline: JobDefinition,
    node: Node,
    parent_handle: Optional[NodeHandle] = None,
) -> Iterable[NodeHandleResourceUse]:
    handle = NodeHandle(node.name, parent_handle)
    if isinstance(node, OpNode):
        for resource_req in node.get_resource_requirements(pipeline.graph):
            if isinstance(resource_req, ResourceKeyRequirement):
                yield NodeHandleResourceUse(resource_req.key, handle)
    elif isinstance(node, GraphNode):
        for nested_node in node.definition.nodes:
            yield from _get_resource_usage_from_node(pipeline, nested_node, handle)


def _get_resource_job_usage(job_defs: Sequence[JobDefinition]) -> ResourceJobUsageMap:
    resource_job_usage_map: dict[str, list[ResourceJobUsageEntry]] = defaultdict(list)

    for job_def in job_defs:
        job_name = job_def.name
        if is_reserved_asset_job_name(job_name):
            continue

        resource_usage: list[NodeHandleResourceUse] = []
        for solid in job_def.nodes_in_topological_order:
            resource_usage += [use for use in _get_resource_usage_from_node(job_def, solid)]
        node_use_by_key: dict[str, list[NodeHandle]] = defaultdict(list)
        for use in resource_usage:
            node_use_by_key[use.resource_key].append(use.node_handle)
        for resource_key in node_use_by_key:
            resource_job_usage_map[resource_key].append(
                ResourceJobUsageEntry(
                    job_name=job_def.name, node_handles=node_use_by_key[resource_key]
                )
            )

    return resource_job_usage_map


def asset_check_node_snaps_from_repo(repo: RepositoryDefinition) -> Sequence[AssetCheckNodeSnap]:
    job_names_by_check_key: dict[AssetCheckKey, list[str]] = defaultdict(list)

    for job_def in repo.get_all_jobs():
        asset_layer = job_def.asset_layer
        for check_key in asset_layer.asset_graph.asset_check_keys:
            job_names_by_check_key[check_key].append(job_def.name)

    asset_check_node_snaps: list[AssetCheckNodeSnap] = []
    for check_key, job_names in job_names_by_check_key.items():
        spec = repo.asset_graph.get_check_spec(check_key)
        automation_condition, automation_condition_snapshot = resolve_automation_condition_args(
            spec.automation_condition
        )
        asset_check_node_snaps.append(
            AssetCheckNodeSnap(
                name=check_key.name,
                asset_key=check_key.asset_key,
                description=spec.description,
                execution_set_identifier=repo.asset_graph.get_execution_set_identifier(check_key),
                job_names=job_names,
                blocking=spec.blocking,
                additional_asset_keys=[dep.asset_key for dep in spec.additional_deps],
                automation_condition=automation_condition,
                automation_condition_snapshot=automation_condition_snapshot,
            )
        )

    return sorted(asset_check_node_snaps, key=lambda check: (check.asset_key, check.name))


def asset_node_snaps_from_repo(repo: RepositoryDefinition) -> Sequence[AssetNodeSnap]:
    # First iterate over all job defs to identify a "primary node" for each materializable asset
    # key. This is the node that will be used to populate the AssetNodeSnap. We need to identify
    # a primary node because the same asset can be materialized as part of multiple jobs.
    primary_node_pairs_by_asset_key: dict[AssetKey, tuple[NodeOutputHandle, JobDefinition]] = {}
    job_defs_by_asset_key: dict[AssetKey, list[JobDefinition]] = defaultdict(list)
    for job_def in repo.get_all_jobs():
        asset_layer = job_def.asset_layer
        for asset_key in asset_layer.external_job_asset_keys:
            job_defs_by_asset_key[asset_key].append(job_def)
        for asset_key in asset_layer.selected_asset_keys:
            job_defs_by_asset_key[asset_key].append(job_def)
            if asset_key not in primary_node_pairs_by_asset_key:
                op_handle = asset_layer.get_op_output_handle(asset_key)
                primary_node_pairs_by_asset_key[asset_key] = (op_handle, job_def)
    asset_node_snaps: list[AssetNodeSnap] = []
    asset_graph = repo.asset_graph
    for key in sorted(asset_graph.get_all_asset_keys()):
        asset_node = asset_graph.get(key)

        # Materializable assets (which are always part of at least one job, due to asset base jobs)
        # have various fields related to their op/output/jobs etc defined. External assets have null
        # values for all these fields.
        if key in primary_node_pairs_by_asset_key:
            output_handle, job_def = primary_node_pairs_by_asset_key[key]

            root_node_handle = output_handle.node_handle.root
            node_def = job_def.graph.get_node(output_handle.node_handle).definition
            node_handles = job_def.asset_layer.upstream_dep_op_handles(key)

            # graph_name is only set for assets that are produced by nested ops.
            graph_name = (
                root_node_handle.name if root_node_handle != output_handle.node_handle else None
            )
            op_defs = [
                cast("OpDefinition", job_def.graph.get_node(node_handle).definition)
                for node_handle in node_handles
                if isinstance(job_def.graph.get_node(node_handle).definition, OpDefinition)
            ]
            pools = {op_def.pool for op_def in op_defs if op_def.pool}
            op_names = sorted([str(handle) for handle in node_handles])
            op_name = graph_name or next(iter(op_names), None) or node_def.name
            compute_kind = node_def.tags.get(COMPUTE_KIND_TAG)
            node_definition_name = node_def.name

            # Confusingly, the `name` field sometimes mismatches the `name` field on the
            # OutputDefinition. We need to fix this.
            output_name = node_def.output_def_named(output_handle.output_name).name
            required_top_level_resources = (
                sorted(node_def.required_resource_keys)
                if isinstance(node_def, OpDefinition)
                else []
            )

        else:
            graph_name = None
            pools = set()
            op_names = []
            op_name = None
            compute_kind = None
            node_definition_name = None
            output_name = None
            required_top_level_resources = []

        # Partition mappings are only exposed on the AssetNodeSnap if at least one asset is
        # partitioned and the partition mapping is one of the builtin types.
        partition_mappings: dict[AssetKey, Optional[PartitionMapping]] = {}
        builtin_partition_mapping_types = get_builtin_partition_mapping_types()
        for pk in asset_node.parent_keys:
            # directly access the partition mapping to avoid the inference step of
            # get_partition_mapping, as we want to defer the inference to the global RemoteAssetGraph
            partition_mapping = repo.asset_graph.get(key).partition_mappings.get(pk)
            if (
                asset_node.partitions_def or repo.asset_graph.get(pk).partitions_def
            ) and isinstance(partition_mapping, builtin_partition_mapping_types):
                partition_mappings[pk] = partition_mapping

        automation_condition, automation_condition_snapshot = resolve_automation_condition_args(
            asset_node.automation_condition
        )
        asset_node_snaps.append(
            AssetNodeSnap(
                asset_key=key,
                parent_edges=[
                    AssetParentEdgeSnap(
                        parent_asset_key=pk, partition_mapping=partition_mappings.get(pk)
                    )
                    for pk in sorted(asset_node.parent_keys)
                ],
                child_edges=[
                    AssetChildEdgeSnap(child_asset_key=k) for k in sorted(asset_node.child_keys)
                ],
                execution_type=asset_node.execution_type,
                compute_kind=compute_kind,
                pools=pools,
                op_name=op_name,
                op_names=op_names,
                code_version=asset_node.code_version,
                node_definition_name=node_definition_name,
                graph_name=graph_name,
                description=asset_node.description,
                job_names=sorted([jd.name for jd in job_defs_by_asset_key[key]]),
                partitions=(
                    PartitionsSnap.from_def(asset_node.partitions_def)
                    if asset_node.partitions_def
                    else None
                ),
                output_name=output_name,
                metadata=asset_node.metadata,
                tags=asset_node.tags,
                group_name=asset_node.group_name,
                legacy_freshness_policy=asset_node.legacy_freshness_policy,
                freshness_policy=asset_node.freshness_policy,
                is_source=asset_node.is_external,
                is_observable=asset_node.is_observable,
                execution_set_identifier=repo.asset_graph.get_execution_set_identifier(key),
                required_top_level_resources=required_top_level_resources,
                auto_materialize_policy=automation_condition.as_auto_materialize_policy()
                if automation_condition
                else None,
                automation_condition_snapshot=automation_condition_snapshot,
                backfill_policy=asset_node.backfill_policy,
                auto_observe_interval_minutes=asset_node.auto_observe_interval_minutes,
                owners=asset_node.owners,
            )
        )

    return asset_node_snaps


def resource_value_snap_from_raw(v: Any) -> ResourceValueSnap:
    if isinstance(v, dict) and set(v.keys()) == {"env"}:
        return ResourceConfigEnvVarSnap(name=v["env"])
    return json.dumps(v)


def _get_nested_resources_map(
    resource_datas: Mapping[str, ResourceDefinition],
    top_level_resources: Mapping[str, ResourceDefinition],
) -> Mapping[str, Mapping[str, NestedResource]]:
    out_map: Mapping[str, Mapping[str, NestedResource]] = {}
    for resource_name, resource_def in resource_datas.items():
        out_map[resource_name] = _get_nested_resources(resource_def, top_level_resources)
    return out_map


def _find_match(nested_resource, resource_defs) -> Optional[str]:
    if is_coercible_to_resource(nested_resource):
        defn = coerce_to_resource(nested_resource)
    else:
        return None

    for k, v in resource_defs.items():
        if defn is v:
            return k

    return None


def _get_nested_resources(
    resource_def: ResourceDefinition,
    top_level_resources: Mapping[str, ResourceDefinition],
) -> Mapping[str, NestedResource]:
    # ConfigurableResources may have "anonymous" nested resources, which are not
    # explicitly specified as top-level resources
    if isinstance(
        resource_def,
        (
            ConfigurableResourceFactoryResourceDefinition,
            ConfigurableIOManagerFactoryResourceDefinition,
        ),
    ):
        results = {}
        for k, nested_resource in resource_def.nested_resources.items():
            top_level_key = _find_match(nested_resource, top_level_resources)
            if top_level_key:
                results[k] = NestedResource(NestedResourceType.TOP_LEVEL, top_level_key)
            else:
                results[k] = NestedResource(
                    NestedResourceType.ANONYMOUS, nested_resource.__class__.__name__
                )
        return results
    else:
        return {
            k: NestedResource(NestedResourceType.TOP_LEVEL, k)
            for k in resource_def.required_resource_keys
        }


def _get_class_name(cls: type) -> str:
    """Returns the fully qualified class name of the given class."""
    return str(cls)[8:-2]


PARTITION_SET_SNAP_NAME_SUFFIX: Final = "_partition_set"


def partition_set_snap_name_for_job_name(job_name) -> str:
    return f"{job_name}{PARTITION_SET_SNAP_NAME_SUFFIX}"


def job_name_for_partition_set_snap_name(name: str) -> str:
    job_name_len = len(name) - len(PARTITION_SET_SNAP_NAME_SUFFIX)
    return name[:job_name_len]


def active_presets_from_job_def(job_def: JobDefinition) -> Sequence[PresetSnap]:
    check.inst_param(job_def, "job_def", JobDefinition)
    if job_def.run_config is None:
        return []
    else:
        return [
            PresetSnap(
                name=DEFAULT_PRESET_NAME,
                run_config=job_def.run_config,
                op_selection=None,
                mode=DEFAULT_MODE_NAME,
                tags={},
            )
        ]


def get_preview_tags(job_def: JobDefinition) -> Mapping[str, str]:
    return {k: v for k, v in job_def.tags.items() if k in TAGS_INCLUDE_IN_REMOTE_JOB_REF}


def resolve_automation_condition_args(
    automation_condition: Optional[AutomationCondition],
) -> tuple[Optional[AutomationCondition], Optional[AutomationConditionSnapshot]]:
    if automation_condition is None:
        return None, None
    elif automation_condition.is_serializable:
        # to avoid serializing too much data, only store the full condition if
        # it is available
        return automation_condition, None
    else:
        # for non-serializable conditions, only include the snapshot
        return None, automation_condition.get_snapshot()


def _extract_fast(serialized_job_data: str):
    target_key = f'"{_JOB_SNAP_STORAGE_FIELD}": '
    target_substr = target_key + get_prefix_for_a_serialized(JobSnap)
    # look for key: type
    idx = serialized_job_data.find(target_substr)
    check.invariant(idx > 0)
    # slice starting after key:
    start_idx = idx + len(target_key)

    # trim outer object }
    # assumption that pipeline_snapshot is last field under test in test_job_data_snap_layout
    serialized_job_snap = serialized_job_data[start_idx:-1]
    check.invariant(serialized_job_snap[0] == "{" and serialized_job_snap[-1] == "}")

    return serialized_job_snap


def _extract_safe(serialized_job_data: str):
    # Intentionally use json directly instead of serdes to avoid losing information if the current process
    # is older than the source process.
    return json.dumps(json.loads(serialized_job_data)[_JOB_SNAP_STORAGE_FIELD])


DISABLE_FAST_EXTRACT_ENV_VAR = "DAGSTER_DISABLE_JOB_SNAP_FAST_EXTRACT"


def extract_serialized_job_snap_from_serialized_job_data_snap(serialized_job_data_snap: str):
    # utility used by DagsterCloudAgent to extract JobSnap out of JobDataSnap
    # efficiently and safely
    if not serialized_job_data_snap.startswith(get_prefix_for_a_serialized(JobDataSnap)):
        raise Exception("Passed in string does not meet expectations for a serialized JobDataSnap")

    if not os.getenv(DISABLE_FAST_EXTRACT_ENV_VAR):
        try:
            return _extract_fast(serialized_job_data_snap)
        except Exception:
            pass

    return _extract_safe(serialized_job_data_snap)


@whitelist_for_serdes
@record
class ComponentInstanceSnap:
    key: str
    full_type_name: str


@whitelist_for_serdes
@record
class ComponentTreeSnap:
    # expect a compact repr for containers & defs components to be added for tree UI
    leaf_instances: Sequence[ComponentInstanceSnap]

    @staticmethod
    def from_tree(tree: ComponentTree) -> "ComponentTreeSnap":
        leaves = []

        for comp_path, comp_inst in check.inst(
            tree.load_root_component(), DefsFolderComponent
        ).iterate_path_component_pairs():
            if not isinstance(
                comp_inst,
                (
                    DefsFolderComponent,
                    CompositeYamlComponent,
                    PythonFileComponent,
                ),
            ):
                cls = comp_inst.__class__
                leaves.append(
                    ComponentInstanceSnap(
                        key=comp_path.get_relative_key(tree.defs_module_path),
                        full_type_name=f"{cls.__module__}.{cls.__qualname__}",
                    )
                )

        return ComponentTreeSnap(leaf_instances=leaves)
