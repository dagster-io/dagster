"""This module contains data objects meant to be serialized between
host processes and user processes. They should contain no
business logic or clever indexing. Use the classes in external.py
for that.
"""

import inspect
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)

import pendulum
from typing_extensions import Final

from dagster import (
    StaticPartitionsDefinition,
    _check as check,
)
from dagster._config.pythonic_config import (
    ConfigurableIOManagerFactoryResourceDefinition,
    ConfigurableResourceFactoryResourceDefinition,
    ResourceWithKeyMapping,
)
from dagster._config.snap import ConfigFieldSnap, ConfigSchemaSnapshot, snap_from_config_type
from dagster._core.definitions import (
    AssetSelection,
    JobDefinition,
    PartitionsDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_sensor_definition import AssetSensorDefinition
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE,
    AssetExecutionType,
)
from dagster._core.definitions.assets import (
    AssetsDefinition,
)
from dagster._core.definitions.assets_job import is_base_asset_job_name
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.auto_materialize_sensor_definition import (
    AutoMaterializeSensorDefinition,
)
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._core.definitions.definition_config_schema import ConfiguredDefinitionConfigSchema
from dagster._core.definitions.dependency import (
    GraphNode,
    Node,
    NodeHandle,
    NodeOutputHandle,
    OpNode,
)
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.metadata import (
    MetadataFieldSerializer,
    MetadataMapping,
    MetadataValue,
    TextMetadataValue,
    normalize_metadata,
)
from dagster._core.definitions.multi_dimensional_partitions import MultiPartitionsDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.partition import DynamicPartitionsDefinition, ScheduleType
from dagster._core.definitions.partition_mapping import (
    PartitionMapping,
    get_builtin_partition_mapping_types,
)
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.schedule_definition import DefaultScheduleStatus
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus,
    SensorDefinition,
    SensorType,
)
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.snap import JobSnapshot
from dagster._core.snap.mode import ResourceDefSnap, build_resource_def_snap
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._serdes import whitelist_for_serdes
from dagster._serdes.serdes import (
    is_whitelisted_for_serdes_object,
)
from dagster._utils.error import SerializableErrorInfo

DEFAULT_MODE_NAME = "default"
DEFAULT_PRESET_NAME = "default"


@whitelist_for_serdes(storage_field_names={"external_job_datas": "external_pipeline_datas"})
class ExternalRepositoryData(
    NamedTuple(
        "_ExternalRepositoryData",
        [
            ("name", str),
            ("external_schedule_datas", Sequence["ExternalScheduleData"]),
            ("external_partition_set_datas", Sequence["ExternalPartitionSetData"]),
            ("external_sensor_datas", Sequence["ExternalSensorData"]),
            ("external_asset_graph_data", Sequence["ExternalAssetNode"]),
            ("external_job_datas", Optional[Sequence["ExternalJobData"]]),
            ("external_job_refs", Optional[Sequence["ExternalJobRef"]]),
            ("external_resource_data", Optional[Sequence["ExternalResourceData"]]),
            ("external_asset_checks", Optional[Sequence["ExternalAssetCheck"]]),
            ("metadata", Optional[MetadataMapping]),
            ("utilized_env_vars", Optional[Mapping[str, Sequence["EnvVarConsumer"]]]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        external_schedule_datas: Sequence["ExternalScheduleData"],
        external_partition_set_datas: Sequence["ExternalPartitionSetData"],
        external_sensor_datas: Optional[Sequence["ExternalSensorData"]] = None,
        external_asset_graph_data: Optional[Sequence["ExternalAssetNode"]] = None,
        external_job_datas: Optional[Sequence["ExternalJobData"]] = None,
        external_job_refs: Optional[Sequence["ExternalJobRef"]] = None,
        external_resource_data: Optional[Sequence["ExternalResourceData"]] = None,
        external_asset_checks: Optional[Sequence["ExternalAssetCheck"]] = None,
        metadata: Optional[MetadataMapping] = None,
        utilized_env_vars: Optional[Mapping[str, Sequence["EnvVarConsumer"]]] = None,
    ):
        return super(ExternalRepositoryData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            external_schedule_datas=check.sequence_param(
                external_schedule_datas, "external_schedule_datas", of_type=ExternalScheduleData
            ),
            external_partition_set_datas=check.sequence_param(
                external_partition_set_datas,
                "external_partition_set_datas",
                of_type=ExternalPartitionSetData,
            ),
            external_sensor_datas=check.opt_sequence_param(
                external_sensor_datas,
                "external_sensor_datas",
                of_type=ExternalSensorData,
            ),
            external_asset_graph_data=check.opt_sequence_param(
                external_asset_graph_data,
                "external_asset_graph_dats",
                of_type=ExternalAssetNode,
            ),
            external_job_datas=check.opt_nullable_sequence_param(
                external_job_datas, "external_job_datas", of_type=ExternalJobData
            ),
            external_job_refs=check.opt_nullable_sequence_param(
                external_job_refs, "external_job_refs", of_type=ExternalJobRef
            ),
            external_resource_data=check.opt_nullable_sequence_param(
                external_resource_data, "external_resource_data", of_type=ExternalResourceData
            ),
            external_asset_checks=check.opt_nullable_sequence_param(
                external_asset_checks,
                "external_asset_checks",
                of_type=ExternalAssetCheck,
            ),
            metadata=check.opt_mapping_param(metadata, "metadata", key_type=str),
            utilized_env_vars=check.opt_nullable_mapping_param(
                utilized_env_vars,
                "utilized_env_vars",
                key_type=str,
            ),
        )

    def has_job_data(self):
        return self.external_job_datas is not None

    def get_external_job_datas(self) -> Sequence["ExternalJobData"]:
        if self.external_job_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")
        return self.external_job_datas

    def get_external_job_refs(self) -> Sequence["ExternalJobRef"]:
        if self.external_job_refs is None:
            check.failed("Snapshots were not deferred, external_job_refs not loaded")
        return self.external_job_refs

    def get_job_snapshot(self, name):
        check.str_param(name, "name")
        if self.external_job_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")

        for external_job_data in self.external_job_datas:
            if external_job_data.name == name:
                return external_job_data.job_snapshot

        check.failed("Could not find pipeline snapshot named " + name)

    def get_external_job_data(self, name):
        check.str_param(name, "name")
        if self.external_job_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")

        for external_job_data in self.external_job_datas:
            if external_job_data.name == name:
                return external_job_data

        check.failed("Could not find external pipeline data named " + name)

    def get_external_schedule_data(self, name):
        check.str_param(name, "name")

        for external_schedule_data in self.external_schedule_datas:
            if external_schedule_data.name == name:
                return external_schedule_data

        check.failed("Could not find external schedule data named " + name)

    def has_external_partition_set_data(self, name) -> bool:
        check.str_param(name, "name")
        for external_partition_set_data in self.external_partition_set_datas:
            if external_partition_set_data.name == name:
                return True

        return False

    def get_external_partition_set_data(self, name) -> "ExternalPartitionSetData":
        check.str_param(name, "name")

        for external_partition_set_data in self.external_partition_set_datas:
            if external_partition_set_data.name == name:
                return external_partition_set_data

        check.failed("Could not find external partition set data named " + name)

    def get_external_sensor_data(self, name):
        check.str_param(name, "name")

        for external_sensor_data in self.external_sensor_datas:
            if external_sensor_data.name == name:
                return external_sensor_data

        check.failed("Could not find sensor data named " + name)


@whitelist_for_serdes(
    storage_name="ExternalPipelineSubsetResult",
    storage_field_names={"external_job_data": "external_pipeline_data"},
)
class ExternalJobSubsetResult(
    NamedTuple(
        "_ExternalJobSubsetResult",
        [
            ("success", bool),
            ("error", Optional[SerializableErrorInfo]),
            ("external_job_data", Optional["ExternalJobData"]),
        ],
    )
):
    def __new__(
        cls,
        success: bool,
        error: Optional[SerializableErrorInfo] = None,
        external_job_data: Optional["ExternalJobData"] = None,
    ):
        return super(ExternalJobSubsetResult, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            external_job_data=check.opt_inst_param(
                external_job_data, "external_job_data", ExternalJobData
            ),
        )


@whitelist_for_serdes(
    storage_name="ExternalPipelineData",
    storage_field_names={
        "job_snapshot": "pipeline_snapshot",
        "parent_job_snapshot": "parent_pipeline_snapshot",
    },
    # There was a period during which `JobDefinition` was a newer subclass of the legacy
    # `PipelineDefinition`, and `is_job` was a boolean field used to distinguish between the two
    # cases on this class.
    old_fields={"is_job": True},
)
class ExternalJobData(
    NamedTuple(
        "_ExternalJobData",
        [
            ("name", str),
            ("job_snapshot", JobSnapshot),
            ("active_presets", Sequence["ExternalPresetData"]),
            ("parent_job_snapshot", Optional[JobSnapshot]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        job_snapshot: JobSnapshot,
        active_presets: Sequence["ExternalPresetData"],
        parent_job_snapshot: Optional[JobSnapshot],
    ):
        return super(ExternalJobData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            job_snapshot=check.inst_param(job_snapshot, "job_snapshot", JobSnapshot),
            parent_job_snapshot=check.opt_inst_param(
                parent_job_snapshot, "parent_job_snapshot", JobSnapshot
            ),
            active_presets=check.sequence_param(
                active_presets, "active_presets", of_type=ExternalPresetData
            ),
        )


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


@whitelist_for_serdes(old_fields={"is_legacy_pipeline": False})
class ExternalJobRef(
    NamedTuple(
        "_ExternalJobRef",
        [
            ("name", str),
            ("snapshot_id", str),
            ("active_presets", Sequence["ExternalPresetData"]),
            ("parent_snapshot_id", Optional[str]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        snapshot_id: str,
        active_presets: Sequence["ExternalPresetData"],
        parent_snapshot_id: Optional[str],
    ):
        return super(ExternalJobRef, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            snapshot_id=check.str_param(snapshot_id, "snapshot_id"),
            active_presets=check.sequence_param(
                active_presets, "active_presets", of_type=ExternalPresetData
            ),
            parent_snapshot_id=check.opt_str_param(parent_snapshot_id, "parent_snapshot_id"),
        )


@whitelist_for_serdes(storage_field_names={"op_selection": "solid_selection"})
class ExternalPresetData(
    NamedTuple(
        "_ExternalPresetData",
        [
            ("name", str),
            ("run_config", Mapping[str, object]),
            ("op_selection", Optional[Sequence[str]]),
            ("mode", str),
            ("tags", Mapping[str, str]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        run_config: Optional[Mapping[str, object]],
        op_selection: Optional[Sequence[str]],
        mode: str,
        tags: Mapping[str, str],
    ):
        return super(ExternalPresetData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            run_config=check.opt_mapping_param(run_config, "run_config", key_type=str),
            op_selection=check.opt_nullable_sequence_param(
                op_selection, "op_selection", of_type=str
            ),
            mode=check.str_param(mode, "mode"),
            tags=check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
        )


@whitelist_for_serdes(
    storage_field_names={"job_name": "pipeline_name", "op_selection": "solid_selection"},
    skip_when_empty_fields={"default_status"},
)
class ExternalScheduleData(
    NamedTuple(
        "_ExternalScheduleData",
        [
            ("name", str),
            ("cron_schedule", Union[str, Sequence[str]]),
            ("job_name", str),
            ("op_selection", Optional[Sequence[str]]),
            ("mode", Optional[str]),
            ("environment_vars", Optional[Mapping[str, str]]),
            ("partition_set_name", Optional[str]),
            ("execution_timezone", Optional[str]),
            ("description", Optional[str]),
            ("default_status", Optional[DefaultScheduleStatus]),
        ],
    )
):
    def __new__(
        cls,
        name,
        cron_schedule,
        job_name,
        op_selection,
        mode,
        environment_vars,
        partition_set_name,
        execution_timezone,
        description=None,
        default_status=None,
    ):
        cron_schedule = check.inst_param(cron_schedule, "cron_schedule", (str, Sequence))
        if not isinstance(cron_schedule, str):
            cron_schedule = check.sequence_param(cron_schedule, "cron_schedule", of_type=str)

        return super(ExternalScheduleData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            cron_schedule=cron_schedule,
            job_name=check.str_param(job_name, "job_name"),
            op_selection=check.opt_nullable_list_param(op_selection, "op_selection", str),
            mode=check.opt_str_param(mode, "mode"),
            environment_vars=check.opt_dict_param(environment_vars, "environment_vars"),
            partition_set_name=check.opt_str_param(partition_set_name, "partition_set_name"),
            execution_timezone=check.opt_str_param(execution_timezone, "execution_timezone"),
            description=check.opt_str_param(description, "description"),
            # Leave default_status as None if it's STOPPED to maintain stable back-compat IDs
            default_status=(
                DefaultScheduleStatus.RUNNING
                if default_status == DefaultScheduleStatus.RUNNING
                else None
            ),
        )


@whitelist_for_serdes
class ExternalScheduleExecutionErrorData(
    NamedTuple("_ExternalScheduleExecutionErrorData", [("error", Optional[SerializableErrorInfo])])
):
    def __new__(cls, error: Optional[SerializableErrorInfo]):
        return super(ExternalScheduleExecutionErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes(
    storage_field_names={"job_name": "pipeline_name", "op_selection": "solid_selection"}
)
class ExternalTargetData(
    NamedTuple(
        "_ExternalTargetData",
        [("job_name", str), ("mode", str), ("op_selection", Optional[Sequence[str]])],
    )
):
    def __new__(cls, job_name: str, mode: str, op_selection: Optional[Sequence[str]]):
        return super(ExternalTargetData, cls).__new__(
            cls,
            job_name=check.str_param(job_name, "job_name"),
            mode=mode,
            op_selection=check.opt_nullable_sequence_param(op_selection, "op_selection", str),
        )


@whitelist_for_serdes
class ExternalSensorMetadata(
    NamedTuple("_ExternalSensorMetadata", [("asset_keys", Optional[Sequence[AssetKey]])])
):
    """Stores additional sensor metadata which is available in the Dagster UI."""

    def __new__(cls, asset_keys: Optional[Sequence[AssetKey]] = None):
        return super(ExternalSensorMetadata, cls).__new__(
            cls,
            asset_keys=check.opt_nullable_sequence_param(
                asset_keys, "asset_keys", of_type=AssetKey
            ),
        )


@whitelist_for_serdes(
    storage_field_names={"job_name": "pipeline_name", "op_selection": "solid_selection"},
    skip_when_empty_fields={"default_status", "sensor_type"},
)
class ExternalSensorData(
    NamedTuple(
        "_ExternalSensorData",
        [
            ("name", str),
            ("job_name", Optional[str]),
            ("op_selection", Optional[Sequence[str]]),
            ("mode", Optional[str]),
            ("min_interval", Optional[int]),
            ("description", Optional[str]),
            ("target_dict", Mapping[str, ExternalTargetData]),
            ("metadata", Optional[ExternalSensorMetadata]),
            ("default_status", Optional[DefaultSensorStatus]),
            ("sensor_type", Optional[SensorType]),
            ("asset_selection", Optional[AssetSelection]),
            ("run_tags", Mapping[str, str]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        job_name: Optional[str] = None,
        op_selection: Optional[Sequence[str]] = None,
        mode: Optional[str] = None,
        min_interval: Optional[int] = None,
        description: Optional[str] = None,
        target_dict: Optional[Mapping[str, ExternalTargetData]] = None,
        metadata: Optional[ExternalSensorMetadata] = None,
        default_status: Optional[DefaultSensorStatus] = None,
        sensor_type: Optional[SensorType] = None,
        asset_selection: Optional[AssetSelection] = None,
        run_tags: Optional[Mapping[str, str]] = None,
    ):
        if job_name and not target_dict:
            # handle the legacy case where the ExternalSensorData was constructed from an earlier
            # version of dagster
            target_dict = {
                job_name: ExternalTargetData(
                    job_name=check.str_param(job_name, "job_name"),
                    mode=check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME),
                    op_selection=check.opt_nullable_sequence_param(
                        op_selection, "op_selection", str
                    ),
                )
            }

        if asset_selection is not None:
            check.opt_inst_param(asset_selection, "asset_selection", AssetSelection)
            check.invariant(
                is_whitelisted_for_serdes_object(asset_selection),
                "asset_selection must be serializable",
            )

        return super(ExternalSensorData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            job_name=check.opt_str_param(job_name, "job_name"),  # keep legacy field populated
            op_selection=check.opt_nullable_sequence_param(
                op_selection, "op_selection", str
            ),  # keep legacy field populated
            mode=check.opt_str_param(mode, "mode"),  # keep legacy field populated
            min_interval=check.opt_int_param(min_interval, "min_interval"),
            description=check.opt_str_param(description, "description"),
            target_dict=check.opt_mapping_param(
                target_dict, "target_dict", str, ExternalTargetData
            ),
            metadata=check.opt_inst_param(metadata, "metadata", ExternalSensorMetadata),
            # Leave default_status as None if it's STOPPED to maintain stable back-compat IDs
            default_status=(
                DefaultSensorStatus.RUNNING
                if default_status == DefaultSensorStatus.RUNNING
                else None
            ),
            sensor_type=sensor_type,
            asset_selection=asset_selection,
            run_tags=run_tags or {},
        )


@whitelist_for_serdes
class ExternalRepositoryErrorData(
    NamedTuple("_ExternalRepositoryErrorData", [("error", Optional[SerializableErrorInfo])])
):
    def __new__(cls, error: Optional[SerializableErrorInfo]):
        return super(ExternalRepositoryErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalSensorExecutionErrorData(
    NamedTuple("_ExternalSensorExecutionErrorData", [("error", Optional[SerializableErrorInfo])])
):
    def __new__(cls, error: Optional[SerializableErrorInfo]):
        return super(ExternalSensorExecutionErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalExecutionParamsData(
    NamedTuple(
        "_ExternalExecutionParamsData",
        [("run_config", Mapping[str, object]), ("tags", Mapping[str, str])],
    )
):
    def __new__(
        cls,
        run_config: Optional[Mapping[str, object]] = None,
        tags: Optional[Mapping[str, str]] = None,
    ):
        return super(ExternalExecutionParamsData, cls).__new__(
            cls,
            run_config=check.opt_mapping_param(run_config, "run_config"),
            tags=check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
        )


@whitelist_for_serdes
class ExternalExecutionParamsErrorData(
    NamedTuple("_ExternalExecutionParamsErrorData", [("error", Optional[SerializableErrorInfo])])
):
    def __new__(cls, error: Optional[SerializableErrorInfo]):
        return super(ExternalExecutionParamsErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


class ExternalPartitionsDefinitionData(ABC):
    @abstractmethod
    def get_partitions_definition(self) -> PartitionsDefinition: ...


@whitelist_for_serdes
class ExternalTimeWindowPartitionsDefinitionData(
    ExternalPartitionsDefinitionData,
    NamedTuple(
        "_ExternalTimeWindowPartitionsDefinitionData",
        [
            ("start", float),
            ("timezone", Optional[str]),
            ("fmt", str),
            ("end_offset", int),
            ("end", Optional[float]),
            ("cron_schedule", Optional[str]),
            # superseded by cron_schedule, but kept around for backcompat
            ("schedule_type", Optional[ScheduleType]),
            # superseded by cron_schedule, but kept around for backcompat
            ("minute_offset", Optional[int]),
            # superseded by cron_schedule, but kept around for backcompat
            ("hour_offset", Optional[int]),
            # superseded by cron_schedule, but kept around for backcompat
            ("day_offset", Optional[int]),
        ],
    ),
):
    def __new__(
        cls,
        start: float,
        timezone: Optional[str],
        fmt: str,
        end_offset: int,
        end: Optional[float] = None,
        cron_schedule: Optional[str] = None,
        schedule_type: Optional[ScheduleType] = None,
        minute_offset: Optional[int] = None,
        hour_offset: Optional[int] = None,
        day_offset: Optional[int] = None,
    ):
        return super(ExternalTimeWindowPartitionsDefinitionData, cls).__new__(
            cls,
            schedule_type=check.opt_inst_param(schedule_type, "schedule_type", ScheduleType),
            start=check.float_param(start, "start"),
            timezone=check.opt_str_param(timezone, "timezone"),
            fmt=check.str_param(fmt, "fmt"),
            end_offset=check.int_param(end_offset, "end_offset"),
            end=check.opt_float_param(end, "end"),
            minute_offset=check.opt_int_param(minute_offset, "minute_offset"),
            hour_offset=check.opt_int_param(hour_offset, "hour_offset"),
            day_offset=check.opt_int_param(day_offset, "day_offset"),
            cron_schedule=check.opt_str_param(cron_schedule, "cron_schedule"),
        )

    def get_partitions_definition(self):
        if self.cron_schedule is not None:
            return TimeWindowPartitionsDefinition(
                cron_schedule=self.cron_schedule,
                start=pendulum.from_timestamp(self.start, tz=self.timezone),
                timezone=self.timezone,
                fmt=self.fmt,
                end_offset=self.end_offset,
                end=pendulum.from_timestamp(self.end, tz=self.timezone) if self.end else None,
            )
        else:
            # backcompat case
            return TimeWindowPartitionsDefinition(
                schedule_type=self.schedule_type,
                start=pendulum.from_timestamp(self.start, tz=self.timezone),
                timezone=self.timezone,
                fmt=self.fmt,
                end_offset=self.end_offset,
                end=pendulum.from_timestamp(self.end, tz=self.timezone) if self.end else None,
                minute_offset=self.minute_offset,
                hour_offset=self.hour_offset,
                day_offset=self.day_offset,
            )


def _dedup_partition_keys(keys: Sequence[str]):
    # Use both a set and a list here to preserve lookup performance in case of large inputs. (We
    # can't just use a set because we need to preserve ordering.)
    seen_keys: Set[str] = set()
    new_keys: List[str] = []
    for key in keys:
        if key not in seen_keys:
            new_keys.append(key)
            seen_keys.add(key)
    return new_keys


@whitelist_for_serdes
class ExternalStaticPartitionsDefinitionData(
    ExternalPartitionsDefinitionData,
    NamedTuple("_ExternalStaticPartitionsDefinitionData", [("partition_keys", Sequence[str])]),
):
    def __new__(cls, partition_keys: Sequence[str]):
        return super(ExternalStaticPartitionsDefinitionData, cls).__new__(
            cls, partition_keys=check.sequence_param(partition_keys, "partition_keys", str)
        )

    def get_partitions_definition(self):
        # v1.4 made `StaticPartitionsDefinition` error if given duplicate keys. This caused
        # host process errors for users who had not upgraded their user code to 1.4 and had dup
        # keys, since the host process `StaticPartitionsDefinition` would throw an error.
        keys = _dedup_partition_keys(self.partition_keys)
        return StaticPartitionsDefinition(keys)


@whitelist_for_serdes
class ExternalPartitionDimensionDefinition(
    NamedTuple(
        "_ExternalPartitionDimensionDefinition",
        [
            ("name", str),
            ("external_partitions_def_data", ExternalPartitionsDefinitionData),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        external_partitions_def_data: ExternalPartitionsDefinitionData,
    ):
        return super(ExternalPartitionDimensionDefinition, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            external_partitions_def_data=check.inst_param(
                external_partitions_def_data,
                "external_partitions_def_data",
                ExternalPartitionsDefinitionData,
            ),
        )


@whitelist_for_serdes
class ExternalMultiPartitionsDefinitionData(
    ExternalPartitionsDefinitionData,
    NamedTuple(
        "_ExternalMultiPartitionsDefinitionData",
        [
            (
                "external_partition_dimension_definitions",
                Sequence[ExternalPartitionDimensionDefinition],
            )
        ],
    ),
):
    def get_partitions_definition(self):
        return MultiPartitionsDefinition(
            {
                partition_dimension.name: (
                    partition_dimension.external_partitions_def_data.get_partitions_definition()
                )
                for partition_dimension in self.external_partition_dimension_definitions
            }
        )


@whitelist_for_serdes
class ExternalDynamicPartitionsDefinitionData(
    ExternalPartitionsDefinitionData,
    NamedTuple("_ExternalDynamicPartitionsDefinitionData", [("name", str)]),
):
    def get_partitions_definition(self):
        return DynamicPartitionsDefinition(name=self.name)


@whitelist_for_serdes(
    storage_field_names={"job_name": "pipeline_name", "op_selection": "solid_selection"}
)
class ExternalPartitionSetData(
    NamedTuple(
        "_ExternalPartitionSetData",
        [
            ("name", str),
            ("job_name", str),
            ("op_selection", Optional[Sequence[str]]),
            ("mode", Optional[str]),
            ("external_partitions_data", Optional[ExternalPartitionsDefinitionData]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        job_name: str,
        op_selection: Optional[Sequence[str]],
        mode: Optional[str],
        external_partitions_data: Optional[ExternalPartitionsDefinitionData] = None,
    ):
        return super(ExternalPartitionSetData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            job_name=check.str_param(job_name, "job_name"),
            op_selection=check.opt_nullable_sequence_param(op_selection, "op_selection", str),
            mode=check.opt_str_param(mode, "mode"),
            external_partitions_data=check.opt_inst_param(
                external_partitions_data,
                "external_partitions_data",
                ExternalPartitionsDefinitionData,
            ),
        )


@whitelist_for_serdes
class ExternalPartitionNamesData(
    NamedTuple("_ExternalPartitionNamesData", [("partition_names", Sequence[str])])
):
    def __new__(cls, partition_names: Optional[Sequence[str]] = None):
        return super(ExternalPartitionNamesData, cls).__new__(
            cls,
            partition_names=check.opt_sequence_param(partition_names, "partition_names", str),
        )


@whitelist_for_serdes
class ExternalPartitionConfigData(
    NamedTuple(
        "_ExternalPartitionConfigData", [("name", str), ("run_config", Mapping[str, object])]
    )
):
    def __new__(cls, name: str, run_config: Optional[Mapping[str, object]] = None):
        return super(ExternalPartitionConfigData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            run_config=check.opt_mapping_param(run_config, "run_config"),
        )


@whitelist_for_serdes
class ExternalPartitionTagsData(
    NamedTuple("_ExternalPartitionTagsData", [("name", str), ("tags", Mapping[str, object])])
):
    def __new__(cls, name: str, tags: Optional[Mapping[str, str]] = None):
        return super(ExternalPartitionTagsData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            tags=check.opt_mapping_param(tags, "tags"),
        )


@whitelist_for_serdes
class ExternalPartitionExecutionParamData(
    NamedTuple(
        "_ExternalPartitionExecutionParamData",
        [("name", str), ("tags", Mapping[str, object]), ("run_config", Mapping[str, object])],
    )
):
    def __new__(cls, name: str, tags: Mapping[str, str], run_config: Mapping[str, object]):
        return super(ExternalPartitionExecutionParamData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            tags=check.mapping_param(tags, "tags"),
            run_config=check.opt_mapping_param(run_config, "run_config"),
        )


@whitelist_for_serdes
class ExternalPartitionSetExecutionParamData(
    NamedTuple(
        "_ExternalPartitionSetExecutionParamData",
        [("partition_data", Sequence[ExternalPartitionExecutionParamData])],
    )
):
    def __new__(cls, partition_data: Sequence[ExternalPartitionExecutionParamData]):
        return super(ExternalPartitionSetExecutionParamData, cls).__new__(
            cls,
            partition_data=check.sequence_param(
                partition_data, "partition_data", of_type=ExternalPartitionExecutionParamData
            ),
        )


@whitelist_for_serdes
class ExternalPartitionExecutionErrorData(
    NamedTuple("_ExternalPartitionExecutionErrorData", [("error", Optional[SerializableErrorInfo])])
):
    def __new__(cls, error: Optional[SerializableErrorInfo]):
        return super(ExternalPartitionExecutionErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalAssetDependency(
    NamedTuple(
        "_ExternalAssetDependency",
        [
            ("upstream_asset_key", AssetKey),
            ("input_name", Optional[str]),
            ("output_name", Optional[str]),
            ("partition_mapping", Optional[PartitionMapping]),
        ],
    )
):
    """A definition of a directed edge in the logical asset graph.

    An upstream asset that's depended on, and the corresponding input name in the downstream asset
    that depends on it.
    """

    def __new__(
        cls,
        upstream_asset_key: AssetKey,
        input_name: Optional[str] = None,
        output_name: Optional[str] = None,
        partition_mapping: Optional[PartitionMapping] = None,
    ):
        return super(ExternalAssetDependency, cls).__new__(
            cls,
            upstream_asset_key=upstream_asset_key,
            input_name=input_name,
            output_name=output_name,
            partition_mapping=partition_mapping,
        )


@whitelist_for_serdes
class ExternalAssetDependedBy(
    NamedTuple(
        "_ExternalAssetDependedBy",
        [
            ("downstream_asset_key", AssetKey),
            ("input_name", Optional[str]),
            ("output_name", Optional[str]),
        ],
    )
):
    """A definition of a directed edge in the logical asset graph.

    An downstream asset that's depended by, and the corresponding input name in the upstream
    asset that it depends on.
    """

    def __new__(
        cls,
        downstream_asset_key: AssetKey,
        input_name: Optional[str] = None,
        output_name: Optional[str] = None,
    ):
        return super(ExternalAssetDependedBy, cls).__new__(
            cls,
            downstream_asset_key=downstream_asset_key,
            input_name=input_name,
            output_name=output_name,
        )


@whitelist_for_serdes
class ExternalResourceConfigEnvVar(NamedTuple):
    name: str


ExternalResourceValue = Union[str, ExternalResourceConfigEnvVar]


UNKNOWN_RESOURCE_TYPE = "Unknown"


@whitelist_for_serdes
class ResourceJobUsageEntry(NamedTuple):
    """Stores information about where a resource is used in a job."""

    job_name: str
    node_handles: List[NodeHandle]


@whitelist_for_serdes
class ExternalResourceData(
    NamedTuple(
        "_ExternalResourceData",
        [
            ("name", str),
            ("resource_snapshot", ResourceDefSnap),
            ("configured_values", Dict[str, ExternalResourceValue]),
            ("config_field_snaps", List[ConfigFieldSnap]),
            ("config_schema_snap", ConfigSchemaSnapshot),
            ("nested_resources", Dict[str, NestedResource]),
            ("parent_resources", Dict[str, str]),
            ("resource_type", str),
            ("is_top_level", bool),
            ("asset_keys_using", List[AssetKey]),
            ("job_ops_using", List[ResourceJobUsageEntry]),
            ("dagster_maintained", bool),
            ("schedules_using", List[str]),
            ("sensors_using", List[str]),
        ],
    )
):
    """Serializable data associated with a top-level resource in a Repository, e.g. one bound using the Definitions API.

    Includes information about the resource definition and config schema, user-passed values, etc.
    """

    def __new__(
        cls,
        name: str,
        resource_snapshot: ResourceDefSnap,
        configured_values: Mapping[str, ExternalResourceValue],
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
        return super(ExternalResourceData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            resource_snapshot=check.inst_param(
                resource_snapshot, "resource_snapshot", ResourceDefSnap
            ),
            configured_values=dict(
                check.mapping_param(
                    configured_values,
                    "configured_values",
                    key_type=str,
                    value_type=(str, ExternalResourceConfigEnvVar),
                )
            ),
            config_field_snaps=check.list_param(
                config_field_snaps, "config_field_snaps", of_type=ConfigFieldSnap
            ),
            config_schema_snap=check.inst_param(
                config_schema_snap, "config_schema_snap", ConfigSchemaSnapshot
            ),
            nested_resources=dict(
                check.opt_mapping_param(
                    nested_resources, "nested_resources", key_type=str, value_type=NestedResource
                )
                or {}
            ),
            parent_resources=dict(
                check.opt_mapping_param(
                    parent_resources, "parent_resources", key_type=str, value_type=str
                )
                or {}
            ),
            is_top_level=check.bool_param(is_top_level, "is_top_level"),
            resource_type=check.str_param(resource_type, "resource_type"),
            asset_keys_using=list(
                check.opt_sequence_param(asset_keys_using, "asset_keys_using", of_type=AssetKey)
            )
            or [],
            job_ops_using=list(
                check.opt_sequence_param(
                    job_ops_using, "job_ops_using", of_type=ResourceJobUsageEntry
                )
            )
            or [],
            dagster_maintained=dagster_maintained,
            schedules_using=list(
                check.opt_sequence_param(schedules_using, "schedules_using", of_type=str)
            ),
            sensors_using=list(
                check.opt_sequence_param(sensors_using, "sensors_using", of_type=str)
            ),
        )


@whitelist_for_serdes(storage_field_names={"execution_set_identifier": "atomic_execution_unit_id"})
class ExternalAssetCheck(
    NamedTuple(
        "_ExternalAssetCheck",
        [
            ("name", str),
            ("asset_key", AssetKey),
            ("description", Optional[str]),
            ("execution_set_identifier", Optional[str]),
            ("job_names", Sequence[str]),
        ],
    )
):
    """Serializable data associated with an asset check."""

    def __new__(
        cls,
        name: str,
        asset_key: AssetKey,
        description: Optional[str],
        execution_set_identifier: Optional[str] = None,
        job_names: Optional[Sequence[str]] = None,
    ):
        return super(ExternalAssetCheck, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            description=check.opt_str_param(description, "description"),
            execution_set_identifier=check.opt_str_param(
                execution_set_identifier, "execution_set_identifier"
            ),
            job_names=check.opt_sequence_param(job_names, "job_names", of_type=str),
        )

    @property
    def key(self) -> AssetCheckKey:
        return AssetCheckKey(asset_key=self.asset_key, name=self.name)


@whitelist_for_serdes(
    storage_field_names={
        "metadata": "metadata_entries",
        "execution_set_identifier": "atomic_execution_unit_id",
    },
    field_serializers={"metadata": MetadataFieldSerializer},
)
class ExternalAssetNode(
    NamedTuple(
        "_ExternalAssetNode",
        [
            ("asset_key", AssetKey),
            ("dependencies", Sequence[ExternalAssetDependency]),
            ("depended_by", Sequence[ExternalAssetDependedBy]),
            ("execution_type", AssetExecutionType),
            ("compute_kind", Optional[str]),
            ("op_name", Optional[str]),
            ("op_names", Sequence[str]),
            ("code_version", Optional[str]),
            ("node_definition_name", Optional[str]),
            ("graph_name", Optional[str]),
            # op_description is a misleading name - this is the description for the asset, not for
            # the op
            ("op_description", Optional[str]),
            ("job_names", Sequence[str]),
            ("partitions_def_data", Optional[ExternalPartitionsDefinitionData]),
            ("output_name", Optional[str]),
            ("output_description", Optional[str]),
            ("metadata", Mapping[str, MetadataValue]),
            ("tags", Optional[Mapping[str, str]]),
            ("group_name", Optional[str]),
            ("freshness_policy", Optional[FreshnessPolicy]),
            ("is_source", bool),
            ("is_observable", bool),
            # If a set of assets can't be materialized independently from each other, they will all
            # have the same execution_set_identifier. This ID should be stable across reloads and
            # unique deployment-wide.
            ("execution_set_identifier", Optional[str]),
            ("required_top_level_resources", Optional[Sequence[str]]),
            ("auto_materialize_policy", Optional[AutoMaterializePolicy]),
            ("backfill_policy", Optional[BackfillPolicy]),
            ("auto_observe_interval_minutes", Optional[float]),
            ("owners", Optional[Sequence[str]]),
        ],
    )
):
    """A definition of a node in the logical asset graph.

    A function for computing the asset and an identifier for that asset.
    """

    def __new__(
        cls,
        asset_key: AssetKey,
        dependencies: Sequence[ExternalAssetDependency],
        depended_by: Sequence[ExternalAssetDependedBy],
        execution_type: Optional[AssetExecutionType] = None,
        compute_kind: Optional[str] = None,
        op_name: Optional[str] = None,
        op_names: Optional[Sequence[str]] = None,
        code_version: Optional[str] = None,
        node_definition_name: Optional[str] = None,
        graph_name: Optional[str] = None,
        op_description: Optional[str] = None,
        job_names: Optional[Sequence[str]] = None,
        partitions_def_data: Optional[ExternalPartitionsDefinitionData] = None,
        output_name: Optional[str] = None,
        output_description: Optional[str] = None,
        metadata: Optional[Mapping[str, MetadataValue]] = None,
        tags: Optional[Mapping[str, str]] = None,
        group_name: Optional[str] = None,
        freshness_policy: Optional[FreshnessPolicy] = None,
        is_source: Optional[bool] = None,
        is_observable: bool = False,
        execution_set_identifier: Optional[str] = None,
        required_top_level_resources: Optional[Sequence[str]] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        auto_observe_interval_minutes: Optional[float] = None,
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

        # backcompat logic to handle ExternalAssetNodes serialized without op_names/graph_name
        if not op_names:
            op_names = list(filter(None, [op_name]))

        # backcompat logic to handle ExternalAssetNodes serialzied without is_source
        if is_source is None:
            # prior to this field being added, all non-source assets must be part of at least one
            # job, and no source assets could be part of any job
            is_source = len(job_names or []) == 0

        return super(ExternalAssetNode, cls).__new__(
            cls,
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            dependencies=check.opt_sequence_param(
                dependencies, "dependencies", of_type=ExternalAssetDependency
            ),
            depended_by=check.opt_sequence_param(
                depended_by, "depended_by", of_type=ExternalAssetDependedBy
            ),
            compute_kind=check.opt_str_param(compute_kind, "compute_kind"),
            op_name=check.opt_str_param(op_name, "op_name"),
            op_names=check.opt_sequence_param(op_names, "op_names"),
            code_version=check.opt_str_param(code_version, "code_version"),
            node_definition_name=check.opt_str_param(node_definition_name, "node_definition_name"),
            graph_name=check.opt_str_param(graph_name, "graph_name"),
            op_description=check.opt_str_param(
                op_description or output_description, "op_description"
            ),
            job_names=check.opt_sequence_param(job_names, "job_names", of_type=str),
            partitions_def_data=check.opt_inst_param(
                partitions_def_data, "partitions_def_data", ExternalPartitionsDefinitionData
            ),
            output_name=check.opt_str_param(output_name, "output_name"),
            output_description=check.opt_str_param(output_description, "output_description"),
            metadata=metadata,
            tags=check.opt_mapping_param(tags, "tags", key_type=str, value_type=str),
            group_name=check.opt_str_param(group_name, "group_name"),
            freshness_policy=check.opt_inst_param(
                freshness_policy, "freshness_policy", FreshnessPolicy
            ),
            is_source=check.bool_param(is_source, "is_source"),
            is_observable=check.bool_param(is_observable, "is_observable"),
            execution_set_identifier=check.opt_str_param(
                execution_set_identifier, "execution_set_identifier"
            ),
            required_top_level_resources=check.opt_sequence_param(
                required_top_level_resources, "required_top_level_resources", of_type=str
            ),
            auto_materialize_policy=check.opt_inst_param(
                auto_materialize_policy,
                "auto_materialize_policy",
                AutoMaterializePolicy,
            ),
            backfill_policy=check.opt_inst_param(
                backfill_policy, "backfill_policy", BackfillPolicy
            ),
            auto_observe_interval_minutes=check.opt_numeric_param(
                auto_observe_interval_minutes, "auto_observe_interval_minutes"
            ),
            owners=check.opt_sequence_param(owners, "owners", of_type=str),
            execution_type=check.inst_param(execution_type, "execution_type", AssetExecutionType),
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


ResourceJobUsageMap = Dict[str, List[ResourceJobUsageEntry]]


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
            yield NodeHandleResourceUse(resource_req.key, handle)
    elif isinstance(node, GraphNode):
        for nested_node in node.definition.nodes:
            yield from _get_resource_usage_from_node(pipeline, nested_node, handle)


def _get_resource_job_usage(job_defs: Sequence[JobDefinition]) -> ResourceJobUsageMap:
    resource_job_usage_map: Dict[str, List[ResourceJobUsageEntry]] = defaultdict(list)

    for job_def in job_defs:
        job_name = job_def.name
        if is_base_asset_job_name(job_name):
            continue

        resource_usage: List[NodeHandleResourceUse] = []
        for solid in job_def.nodes_in_topological_order:
            resource_usage += [use for use in _get_resource_usage_from_node(job_def, solid)]
        node_use_by_key: Dict[str, List[NodeHandle]] = defaultdict(list)
        for use in resource_usage:
            node_use_by_key[use.resource_key].append(use.node_handle)
        for resource_key in node_use_by_key:
            resource_job_usage_map[resource_key].append(
                ResourceJobUsageEntry(job_def.name, node_use_by_key[resource_key])
            )

    return resource_job_usage_map


def external_repository_data_from_def(
    repository_def: RepositoryDefinition,
    defer_snapshots: bool = False,
) -> ExternalRepositoryData:
    check.inst_param(repository_def, "repository_def", RepositoryDefinition)

    jobs = repository_def.get_all_jobs()
    if defer_snapshots:
        job_datas = None
        job_refs = sorted(
            list(map(external_job_ref_from_def, jobs)),
            key=lambda pd: pd.name,
        )
    else:
        job_datas = sorted(
            list(
                map(lambda job: external_job_data_from_def(job, include_parent_snapshot=True), jobs)
            ),
            key=lambda pd: pd.name,
        )
        job_refs = None

    resource_datas = repository_def.get_top_level_resources()
    asset_graph = external_asset_nodes_from_defs(
        jobs,
        repository_def.asset_graph,
    )

    nested_resource_map = _get_nested_resources_map(
        resource_datas, repository_def.get_resource_key_mapping()
    )
    inverted_nested_resources_map: Dict[str, Dict[str, str]] = defaultdict(dict)
    for resource_key, nested_resources in nested_resource_map.items():
        for attribute, nested_resource in nested_resources.items():
            if nested_resource.type == NestedResourceType.TOP_LEVEL:
                inverted_nested_resources_map[nested_resource.name][resource_key] = attribute

    resource_asset_usage_map: Dict[str, List[AssetKey]] = defaultdict(list)
    # collect resource usage from normal non-source assets
    for asset in asset_graph:
        if asset.required_top_level_resources:
            for resource_key in asset.required_top_level_resources:
                resource_asset_usage_map[resource_key].append(asset.asset_key)

    resource_schedule_usage_map: Dict[str, List[str]] = defaultdict(list)
    for schedule in repository_def.schedule_defs:
        if schedule.required_resource_keys:
            for resource_key in schedule.required_resource_keys:
                resource_schedule_usage_map[resource_key].append(schedule.name)

    resource_sensor_usage_map: Dict[str, List[str]] = defaultdict(list)
    for sensor in repository_def.sensor_defs:
        if sensor.required_resource_keys:
            for resource_key in sensor.required_resource_keys:
                resource_sensor_usage_map[resource_key].append(sensor.name)

    resource_job_usage_map: ResourceJobUsageMap = _get_resource_job_usage(jobs)

    return ExternalRepositoryData(
        name=repository_def.name,
        external_schedule_datas=sorted(
            list(map(external_schedule_data_from_def, repository_def.schedule_defs)),
            key=lambda sd: sd.name,
        ),
        # `PartitionSetDefinition` has been deleted, so we now construct `ExternalPartitonSetData`
        # from jobs instead of going through the intermediary `PartitionSetDefinition`. Eventually
        # we will remove `ExternalPartitionSetData` as well.
        external_partition_set_datas=sorted(
            filter(
                None,
                [
                    external_partition_set_data_from_def(job_def)
                    for job_def in repository_def.get_all_jobs()
                ],
            ),
            key=lambda psd: psd.name,
        ),
        external_sensor_datas=sorted(
            [
                external_sensor_data_from_def(sensor_def, repository_def)
                for sensor_def in repository_def.sensor_defs
            ],
            key=lambda sd: sd.name,
        ),
        external_asset_graph_data=asset_graph,
        external_job_datas=job_datas,
        external_job_refs=job_refs,
        external_resource_data=sorted(
            [
                external_resource_data_from_def(
                    res_name,
                    res_data,
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
        external_asset_checks=external_asset_checks_from_defs(jobs),
        metadata=repository_def.metadata,
        utilized_env_vars={
            env_var: [
                EnvVarConsumer(type=EnvVarConsumerType.RESOURCE, name=res_name)
                for res_name in res_names
            ]
            for env_var, res_names in repository_def.get_env_vars_by_top_level_resource().items()
        },
    )


def external_asset_checks_from_defs(
    job_defs: Sequence[JobDefinition],
) -> Sequence[ExternalAssetCheck]:
    nodes_by_check_key: Dict[AssetCheckKey, List[AssetsDefinition]] = {}
    job_names_by_check_key: Dict[AssetCheckKey, List[str]] = {}

    for job_def in job_defs:
        asset_layer = job_def.asset_layer
        for asset_def in asset_layer.assets_defs_by_node_handle.values():
            for spec in asset_def.check_specs:
                nodes_by_check_key.setdefault(spec.key, []).append(asset_def)
                job_names_by_check_key.setdefault(spec.key, []).append(job_def.name)

    external_checks = []
    for check_key, nodes in nodes_by_check_key.items():
        first_node = nodes[0]
        # The same check may appear multiple times in different jobs, but it should come from the
        # same definition.
        check.is_list(
            nodes,
            of_type=AssetsDefinition,
            additional_message=f"Check {check_key} is redefined in an AssetsDefinition and an AssetChecksDefinition",
        )

        # Executing individual checks isn't supported in graph assets
        if isinstance(first_node.node_def, GraphDefinition):
            execution_set_identifier = first_node.unique_id
        else:
            execution_set_identifier = first_node.unique_id if not first_node.can_subset else None

        spec = first_node.get_spec_for_check_key(check_key)
        external_checks.append(
            ExternalAssetCheck(
                name=check_key.name,
                asset_key=check_key.asset_key,
                description=spec.description,
                execution_set_identifier=execution_set_identifier,
                job_names=job_names_by_check_key[check_key],
            )
        )

    return sorted(external_checks, key=lambda check: (check.asset_key, check.name))


def external_asset_nodes_from_defs(
    job_defs: Sequence[JobDefinition],
    asset_graph: AssetGraph,
) -> Sequence[ExternalAssetNode]:
    # First iterate over all job defs to identify a "primary node" for each materializable asset
    # key. This is the node that will be used to populate the ExternalAssetNode. We need to identify
    # a primary node because the same asset can be materialized as part of multiple jobs.
    primary_node_pairs_by_asset_key: Dict[AssetKey, Tuple[NodeOutputHandle, JobDefinition]] = {}
    job_defs_by_asset_key: Dict[AssetKey, List[JobDefinition]] = {}
    for job_def in job_defs:
        asset_layer = job_def.asset_layer
        asset_info_by_node_output = asset_layer.asset_info_by_node_output_handle
        for node_output_handle, asset_info in asset_info_by_node_output.items():
            asset_key = asset_info.key
            if not asset_info.is_required:
                continue
            if asset_key not in primary_node_pairs_by_asset_key:
                primary_node_pairs_by_asset_key[asset_key] = (node_output_handle, job_def)
            job_defs_by_asset_key.setdefault(asset_key, []).append(job_def)

    # Build index of execution set identifiers. Only assets that are part of non-subsettable assets
    # have a defined execution set identifier.
    execution_set_identifiers_by_asset_key: Dict[AssetKey, str] = {}
    for assets_def in asset_graph.assets_defs:
        if (len(assets_def.keys) > 1 or assets_def.check_keys) and not assets_def.can_subset:
            execution_set_identifiers_by_asset_key.update(
                {k: assets_def.unique_id for k in assets_def.keys}
            )

    external_asset_nodes: List[ExternalAssetNode] = []
    for key in sorted(asset_graph.all_asset_keys):
        asset_node = asset_graph.get(key)

        # Materializable assets (which are always part of at least one job, due to asset base jobs)
        # have various fields related to their op/output/jobs etc defined. External assets have null
        # values for all these fields.
        if key in primary_node_pairs_by_asset_key:
            output_handle, job_def = primary_node_pairs_by_asset_key[key]

            root_node_handle = output_handle.node_handle
            while True:
                if root_node_handle.parent is None:
                    break
                root_node_handle = root_node_handle.parent
            node_def = job_def.graph.get_node(output_handle.node_handle).definition
            node_handles = job_def.asset_layer.dependency_node_handles_by_asset_key.get(key, [])

            # graph_name is only set for assets that are produced by nested ops.
            graph_name = (
                root_node_handle.name if root_node_handle != output_handle.node_handle else None
            )
            op_names = sorted([str(handle) for handle in node_handles])
            op_name = graph_name or next(iter(op_names), None) or node_def.name
            job_names = sorted([jd.name for jd in job_defs_by_asset_key[key]])
            compute_kind = node_def.tags.get("kind")
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
            op_names = []
            op_name = None
            job_names = []
            compute_kind = None
            node_definition_name = None
            output_name = None
            required_top_level_resources = []

        # This is in place to preserve an implicit behavior in the Dagster UI where stub
        # dependencies were rendered as if they weren't part of the default asset group.
        group_name = None if asset_node.assets_def.is_auto_created_stub else asset_node.group_name

        # Partition mappings are only exposed on the ExternalAssetNode if at least one asset is
        # partitioned and the partition mapping is one of the builtin types.
        partition_mappings: Dict[AssetKey, Optional[PartitionMapping]] = {}
        builtin_partition_mapping_types = get_builtin_partition_mapping_types()
        for pk in asset_node.parent_keys:
            partition_mapping = asset_graph.get_partition_mapping(key, pk)
            if (asset_node.partitions_def or asset_graph.get(pk).partitions_def) and isinstance(
                partition_mapping, builtin_partition_mapping_types
            ):
                partition_mappings[pk] = partition_mapping

        external_asset_nodes.append(
            ExternalAssetNode(
                asset_key=key,
                dependencies=[
                    ExternalAssetDependency(
                        upstream_asset_key=pk, partition_mapping=partition_mappings.get(pk)
                    )
                    for pk in sorted(asset_node.parent_keys)
                ],
                depended_by=[ExternalAssetDependedBy(k) for k in sorted(asset_node.child_keys)],
                execution_type=asset_node.execution_type,
                compute_kind=compute_kind,
                op_name=op_name,
                op_names=op_names,
                code_version=asset_node.code_version,
                node_definition_name=node_definition_name,
                graph_name=graph_name,
                op_description=asset_node.description,
                job_names=job_names,
                partitions_def_data=(
                    external_partitions_definition_from_def(asset_node.partitions_def)
                    if asset_node.partitions_def
                    else None
                ),
                output_name=output_name,
                metadata=asset_node.metadata,
                tags=asset_node.tags,
                group_name=group_name,
                freshness_policy=asset_node.freshness_policy,
                is_source=asset_node.is_external,
                is_observable=asset_node.is_observable,
                execution_set_identifier=execution_set_identifiers_by_asset_key.get(key),
                required_top_level_resources=required_top_level_resources,
                auto_materialize_policy=asset_node.auto_materialize_policy,
                backfill_policy=asset_node.backfill_policy,
                auto_observe_interval_minutes=asset_node.auto_observe_interval_minutes,
                owners=asset_node.owners,
            )
        )

    return external_asset_nodes


def external_job_data_from_def(
    job_def: JobDefinition, include_parent_snapshot: bool
) -> ExternalJobData:
    check.inst_param(job_def, "job_def", JobDefinition)
    return ExternalJobData(
        name=job_def.name,
        job_snapshot=job_def.get_job_snapshot(),
        parent_job_snapshot=job_def.get_parent_job_snapshot() if include_parent_snapshot else None,
        active_presets=active_presets_from_job_def(job_def),
    )


def external_job_ref_from_def(job_def: JobDefinition) -> ExternalJobRef:
    check.inst_param(job_def, "job_def", JobDefinition)

    return ExternalJobRef(
        name=job_def.name,
        snapshot_id=job_def.get_job_snapshot_id(),
        parent_snapshot_id=None,
        active_presets=active_presets_from_job_def(job_def),
    )


def external_resource_value_from_raw(v: Any) -> ExternalResourceValue:
    if isinstance(v, dict) and set(v.keys()) == {"env"}:
        return ExternalResourceConfigEnvVar(name=v["env"])
    return json.dumps(v)


def _get_nested_resources_map(
    resource_datas: Mapping[str, ResourceDefinition], resource_key_mapping: Mapping[int, str]
) -> Mapping[str, Mapping[str, NestedResource]]:
    out_map: Mapping[str, Mapping[str, NestedResource]] = {}
    for resource_name, resource_def in resource_datas.items():
        out_map[resource_name] = _get_nested_resources(resource_def, resource_key_mapping)
    return out_map


def _get_nested_resources(
    resource_def: ResourceDefinition, resource_key_mapping: Mapping[int, str]
) -> Mapping[str, NestedResource]:
    if isinstance(resource_def, ResourceWithKeyMapping):
        resource_def = resource_def.wrapped_resource

    # ConfigurableResources may have "anonymous" nested resources, which are not
    # explicitly specified as top-level resources
    if isinstance(
        resource_def,
        (
            ConfigurableResourceFactoryResourceDefinition,
            ConfigurableIOManagerFactoryResourceDefinition,
        ),
    ):
        return {
            k: (
                NestedResource(
                    NestedResourceType.TOP_LEVEL, resource_key_mapping[id(nested_resource)]
                )
                if id(nested_resource) in resource_key_mapping
                else NestedResource(
                    NestedResourceType.ANONYMOUS, nested_resource.__class__.__name__
                )
            )
            for k, nested_resource in resource_def.nested_resources.items()
        }
    else:
        return {
            k: NestedResource(NestedResourceType.TOP_LEVEL, k)
            for k in resource_def.required_resource_keys
        }


def _get_class_name(cls: Type) -> str:
    """Returns the fully qualified class name of the given class."""
    return str(cls)[8:-2]


def external_resource_data_from_def(
    name: str,
    resource_def: ResourceDefinition,
    nested_resources: Mapping[str, NestedResource],
    parent_resources: Mapping[str, str],
    resource_asset_usage_map: Mapping[str, List[AssetKey]],
    resource_job_usage_map: ResourceJobUsageMap,
    resource_schedule_usage_map: Mapping[str, List[str]],
    resource_sensor_usage_map: Mapping[str, List[str]],
) -> ExternalResourceData:
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
        Mapping[str, Any],
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
        k: external_resource_value_from_raw(v) for k, v in config_schema_default.items()
    }

    resource_type_def = resource_def
    if isinstance(resource_type_def, ResourceWithKeyMapping):
        resource_type_def = resource_type_def.wrapped_resource

    # use the resource function name as the resource type if it's a function resource
    # (ie direct instantiation of ResourceDefinition or IOManagerDefinition)
    if type(resource_type_def) in (ResourceDefinition, IOManagerDefinition):
        original_resource_fn = (
            resource_type_def._hardcoded_resource_type  # noqa: SLF001
            if resource_type_def._hardcoded_resource_type  # noqa: SLF001
            else resource_type_def.resource_fn
        )
        module_name = check.not_none(inspect.getmodule(original_resource_fn)).__name__
        resource_type = f"{module_name}.{original_resource_fn.__name__}"
    # if it's a Pythonic resource, get the underlying Pythonic class name
    elif isinstance(
        resource_type_def,
        (
            ConfigurableResourceFactoryResourceDefinition,
            ConfigurableIOManagerFactoryResourceDefinition,
        ),
    ):
        resource_type = _get_class_name(resource_type_def.configurable_resource_cls)
    else:
        resource_type = _get_class_name(type(resource_type_def))

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

    return ExternalResourceData(
        name=name,
        resource_snapshot=build_resource_def_snap(name, resource_def),
        configured_values=configured_values,
        config_field_snaps=unconfigured_config_type_snap.fields or [],
        config_schema_snap=config_type.get_schema_snapshot(),
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


def external_schedule_data_from_def(schedule_def: ScheduleDefinition) -> ExternalScheduleData:
    check.inst_param(schedule_def, "schedule_def", ScheduleDefinition)
    return ExternalScheduleData(
        name=schedule_def.name,
        cron_schedule=schedule_def.cron_schedule,
        job_name=schedule_def.job_name,
        op_selection=schedule_def._target.op_selection,  # noqa: SLF001
        mode=DEFAULT_MODE_NAME,
        environment_vars=schedule_def.environment_vars,
        partition_set_name=None,
        execution_timezone=schedule_def.execution_timezone,
        description=schedule_def.description,
        default_status=schedule_def.default_status,
    )


def external_partitions_definition_from_def(
    partitions_def: PartitionsDefinition,
) -> ExternalPartitionsDefinitionData:
    if isinstance(partitions_def, TimeWindowPartitionsDefinition):
        return external_time_window_partitions_definition_from_def(partitions_def)
    elif isinstance(partitions_def, StaticPartitionsDefinition):
        return external_static_partitions_definition_from_def(partitions_def)
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        return external_multi_partitions_definition_from_def(partitions_def)
    elif isinstance(partitions_def, DynamicPartitionsDefinition):
        return external_dynamic_partitions_definition_from_def(partitions_def)
    else:
        raise DagsterInvalidDefinitionError(
            "Only static, time window, multi-dimensional partitions, and dynamic partitions"
            " definitions with a name parameter are currently supported."
        )


def external_time_window_partitions_definition_from_def(
    partitions_def: TimeWindowPartitionsDefinition,
) -> ExternalTimeWindowPartitionsDefinitionData:
    check.inst_param(partitions_def, "partitions_def", TimeWindowPartitionsDefinition)
    return ExternalTimeWindowPartitionsDefinitionData(
        cron_schedule=partitions_def.cron_schedule,
        start=pendulum.instance(partitions_def.start, tz=partitions_def.timezone).timestamp(),
        end=(
            pendulum.instance(partitions_def.end, tz=partitions_def.timezone).timestamp()
            if partitions_def.end
            else None
        ),
        timezone=partitions_def.timezone,
        fmt=partitions_def.fmt,
        end_offset=partitions_def.end_offset,
    )


def external_static_partitions_definition_from_def(
    partitions_def: StaticPartitionsDefinition,
) -> ExternalStaticPartitionsDefinitionData:
    check.inst_param(partitions_def, "partitions_def", StaticPartitionsDefinition)
    return ExternalStaticPartitionsDefinitionData(
        partition_keys=partitions_def.get_partition_keys()
    )


def external_multi_partitions_definition_from_def(
    partitions_def: MultiPartitionsDefinition,
) -> ExternalMultiPartitionsDefinitionData:
    check.inst_param(partitions_def, "partitions_def", MultiPartitionsDefinition)

    return ExternalMultiPartitionsDefinitionData(
        external_partition_dimension_definitions=[
            ExternalPartitionDimensionDefinition(
                dimension.name,
                external_partitions_definition_from_def(dimension.partitions_def),
            )
            for dimension in partitions_def.partitions_defs
        ]
    )


def external_dynamic_partitions_definition_from_def(
    partitions_def: DynamicPartitionsDefinition,
) -> ExternalDynamicPartitionsDefinitionData:
    check.inst_param(partitions_def, "partitions_def", DynamicPartitionsDefinition)
    if partitions_def.name is None:
        raise DagsterInvalidDefinitionError(
            "Dagster does not support dynamic partitions definitions without a name parameter."
        )
    return ExternalDynamicPartitionsDefinitionData(name=partitions_def.name)


def external_partition_set_data_from_def(
    job_def: JobDefinition,
) -> Optional[ExternalPartitionSetData]:
    check.inst_param(job_def, "job_def", JobDefinition)

    partitions_def = job_def.partitions_def
    if partitions_def is None:
        return None

    partitions_def_data: Optional[ExternalPartitionsDefinitionData] = None
    if isinstance(partitions_def, TimeWindowPartitionsDefinition):
        partitions_def_data = external_time_window_partitions_definition_from_def(partitions_def)
    elif isinstance(partitions_def, StaticPartitionsDefinition):
        partitions_def_data = external_static_partitions_definition_from_def(partitions_def)
    elif (
        isinstance(partitions_def, DynamicPartitionsDefinition) and partitions_def.name is not None
    ):
        partitions_def_data = external_dynamic_partitions_definition_from_def(partitions_def)
    elif isinstance(partitions_def, MultiPartitionsDefinition):
        partitions_def_data = external_multi_partitions_definition_from_def(partitions_def)
    else:
        partitions_def_data = None

    return ExternalPartitionSetData(
        name=external_partition_set_name_for_job_name(job_def.name),
        job_name=job_def.name,
        op_selection=None,
        mode=DEFAULT_MODE_NAME,
        external_partitions_data=partitions_def_data,
    )


EXTERNAL_PARTITION_SET_NAME_SUFFIX: Final = "_partition_set"


def external_partition_set_name_for_job_name(job_name) -> str:
    return f"{job_name}{EXTERNAL_PARTITION_SET_NAME_SUFFIX}"


def job_name_for_external_partition_set_name(name: str) -> str:
    job_name_len = len(name) - len(EXTERNAL_PARTITION_SET_NAME_SUFFIX)
    return name[:job_name_len]


def external_sensor_data_from_def(
    sensor_def: SensorDefinition, repository_def: RepositoryDefinition
) -> ExternalSensorData:
    first_target = sensor_def.targets[0] if sensor_def.targets else None

    asset_keys = None
    if isinstance(sensor_def, AssetSensorDefinition):
        asset_keys = [sensor_def.asset_key]

    if sensor_def.asset_selection is not None:
        target_dict = {
            base_asset_job_name: ExternalTargetData(
                job_name=base_asset_job_name, mode=DEFAULT_MODE_NAME, op_selection=None
            )
            for base_asset_job_name in repository_def.get_implicit_asset_job_names()
        }

        serializable_asset_selection = sensor_def.asset_selection.to_serializable_asset_selection(
            repository_def.asset_graph
        )
    else:
        target_dict = {
            target.job_name: ExternalTargetData(
                job_name=target.job_name,
                mode=DEFAULT_MODE_NAME,
                op_selection=target.op_selection,
            )
            for target in sensor_def.targets
        }

        serializable_asset_selection = None

    return ExternalSensorData(
        name=sensor_def.name,
        job_name=first_target.job_name if first_target else None,
        mode=None,
        op_selection=first_target.op_selection if first_target else None,
        target_dict=target_dict,
        min_interval=sensor_def.minimum_interval_seconds,
        description=sensor_def.description,
        metadata=ExternalSensorMetadata(asset_keys=asset_keys),
        default_status=sensor_def.default_status,
        sensor_type=sensor_def.sensor_type,
        asset_selection=serializable_asset_selection,
        run_tags=(
            sensor_def.run_tags if isinstance(sensor_def, AutoMaterializeSensorDefinition) else None
        ),
    )


def active_presets_from_job_def(job_def: JobDefinition) -> Sequence[ExternalPresetData]:
    check.inst_param(job_def, "job_def", JobDefinition)
    if job_def.run_config is None:
        return []
    else:
        return [
            ExternalPresetData(
                name=DEFAULT_PRESET_NAME,
                run_config=job_def.run_config,
                op_selection=None,
                mode=DEFAULT_MODE_NAME,
                tags={},
            )
        ]
