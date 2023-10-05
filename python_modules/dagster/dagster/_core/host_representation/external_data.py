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
    TYPE_CHECKING,
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
    JobDefinition,
    PartitionsDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
    SourceAsset,
)
from dagster._core.definitions.asset_check_spec import AssetCheckKey
from dagster._core.definitions.asset_sensor_definition import AssetSensorDefinition
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE,
    AssetExecutionType,
)
from dagster._core.definitions.assets_job import is_base_asset_job_name
from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
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
from dagster._core.definitions.metadata import (
    MetadataFieldSerializer,
    MetadataMapping,
    MetadataUserInput,
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
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.snap import JobSnapshot
from dagster._core.snap.mode import ResourceDefSnap, build_resource_def_snap
from dagster._core.storage.io_manager import IOManagerDefinition
from dagster._serdes import whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo

if TYPE_CHECKING:
    from dagster._core.definitions.asset_layer import AssetOutputInfo

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

    def get_external_partition_set_data(self, name):
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
            default_status=(
                DefaultSensorStatus.RUNNING
                if default_status == DefaultSensorStatus.RUNNING
                else None
            ),
            sensor_type=sensor_type,
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


@whitelist_for_serdes
class ExternalAssetCheck(
    NamedTuple(
        "_ExternalAssetCheck",
        [
            ("name", str),
            ("asset_key", AssetKey),
            ("description", Optional[str]),
            ("atomic_execution_unit_id", Optional[str]),
        ],
    )
):
    """Serializable data associated with an asset check."""

    def __new__(
        cls,
        name: str,
        asset_key: AssetKey,
        description: Optional[str],
        atomic_execution_unit_id: Optional[str] = None,
    ):
        return super(ExternalAssetCheck, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            asset_key=check.inst_param(asset_key, "asset_key", AssetKey),
            description=check.opt_str_param(description, "description"),
            atomic_execution_unit_id=check.opt_str_param(
                atomic_execution_unit_id, "automic_execution_unit_id"
            ),
        )

    @property
    def key(self) -> AssetCheckKey:
        return AssetCheckKey(asset_key=self.asset_key, name=self.name)


@whitelist_for_serdes(
    storage_field_names={"metadata": "metadata_entries"},
    field_serializers={"metadata": MetadataFieldSerializer},
)
class ExternalAssetNode(
    NamedTuple(
        "_ExternalAssetNode",
        [
            ("asset_key", AssetKey),
            ("dependencies", Sequence[ExternalAssetDependency]),
            ("depended_by", Sequence[ExternalAssetDependedBy]),
            ("compute_kind", Optional[str]),
            ("op_name", Optional[str]),
            ("op_names", Optional[Sequence[str]]),
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
            ("group_name", Optional[str]),
            ("freshness_policy", Optional[FreshnessPolicy]),
            ("is_source", bool),
            ("is_observable", bool),
            # If a set of assets can't be materialized independently from each other, they will all
            # have the same atomic_execution_unit_id. This ID should be stable across reloads and
            # unique deployment-wide.
            ("atomic_execution_unit_id", Optional[str]),
            ("required_top_level_resources", Optional[Sequence[str]]),
            ("auto_materialize_policy", Optional[AutoMaterializePolicy]),
            ("backfill_policy", Optional[BackfillPolicy]),
            ("auto_observe_interval_minutes", Optional[float]),
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
        group_name: Optional[str] = None,
        freshness_policy: Optional[FreshnessPolicy] = None,
        is_source: Optional[bool] = None,
        is_observable: bool = False,
        atomic_execution_unit_id: Optional[str] = None,
        required_top_level_resources: Optional[Sequence[str]] = None,
        auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
        backfill_policy: Optional[BackfillPolicy] = None,
        auto_observe_interval_minutes: Optional[float] = None,
    ):
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
            metadata=normalize_metadata(
                check.opt_mapping_param(metadata, "metadata", key_type=str)
            ),
            group_name=check.opt_str_param(group_name, "group_name"),
            freshness_policy=check.opt_inst_param(
                freshness_policy, "freshness_policy", FreshnessPolicy
            ),
            is_source=check.bool_param(is_source, "is_source"),
            is_observable=check.bool_param(is_observable, "is_observable"),
            atomic_execution_unit_id=check.opt_str_param(
                atomic_execution_unit_id, "atomic_execution_unit_id"
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
        )

    @property
    def is_executable(self) -> bool:
        metadata_value = self.metadata.get(SYSTEM_METADATA_KEY_ASSET_EXECUTION_TYPE)
        if not metadata_value:
            varietal_text = None
        else:
            check.inst(metadata_value, TextMetadataValue)  # for guaranteed runtime error
            assert isinstance(metadata_value, TextMetadataValue)  # for type checker
            varietal_text = metadata_value.value

        return AssetExecutionType.is_executable(varietal_text)


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
            list(map(external_job_data_from_def, jobs)),
            key=lambda pd: pd.name,
        )
        job_refs = None

    resource_datas = repository_def.get_top_level_resources()
    asset_graph = external_asset_nodes_from_defs(
        jobs,
        source_assets_by_key=repository_def.source_assets_by_key,
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

    # collect resource usage from source assets
    for source_asset_key, source_asset in repository_def.source_assets_by_key.items():
        if source_asset.required_resource_keys:
            for resource_key in source_asset.required_resource_keys:
                resource_asset_usage_map[resource_key].append(source_asset_key)

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
    # put specs in a dict to dedupe, since the same check can exist in multiple jobs
    check_specs_dict = {}
    for job_def in job_defs:
        asset_layer = job_def.asset_layer

        # checks defined with @asset_check
        for asset_check_def in asset_layer.asset_checks_defs:
            for spec in asset_check_def.specs:
                check_specs_dict[(spec.asset_key, spec.name)] = ExternalAssetCheck(
                    name=spec.name, asset_key=spec.asset_key, description=spec.description
                )

        # checks defined on @asset
        for asset_def in asset_layer.assets_defs_by_key.values():
            for spec in asset_def.check_specs:
                atomic_execution_unit_id = asset_def.unique_id if not asset_def.can_subset else None
                check_specs_dict[(spec.asset_key, spec.name)] = ExternalAssetCheck(
                    name=spec.name,
                    asset_key=spec.asset_key,
                    description=spec.description,
                    atomic_execution_unit_id=atomic_execution_unit_id,
                )

    return sorted(check_specs_dict.values(), key=lambda check: (check.asset_key, check.name))


def external_asset_nodes_from_defs(
    job_defs: Sequence[JobDefinition],
    source_assets_by_key: Mapping[AssetKey, SourceAsset],
) -> Sequence[ExternalAssetNode]:
    node_defs_by_asset_key: Dict[AssetKey, List[Tuple[NodeOutputHandle, JobDefinition]]] = (
        defaultdict(list)
    )
    asset_info_by_asset_key: Dict[AssetKey, AssetOutputInfo] = dict()
    freshness_policy_by_asset_key: Dict[AssetKey, FreshnessPolicy] = dict()
    metadata_by_asset_key: Dict[AssetKey, MetadataUserInput] = dict()
    auto_materialize_policy_by_asset_key: Dict[AssetKey, AutoMaterializePolicy] = dict()
    backfill_policy_by_asset_key: Dict[AssetKey, Optional[BackfillPolicy]] = dict()

    deps: Dict[AssetKey, Dict[AssetKey, ExternalAssetDependency]] = defaultdict(dict)
    dep_by: Dict[AssetKey, Dict[AssetKey, ExternalAssetDependedBy]] = defaultdict(dict)
    all_upstream_asset_keys: Set[AssetKey] = set()
    op_names_by_asset_key: Dict[AssetKey, Sequence[str]] = {}
    code_version_by_asset_key: Dict[AssetKey, Optional[str]] = dict()
    group_name_by_asset_key: Dict[AssetKey, str] = {}
    descriptions_by_asset_key: Dict[AssetKey, str] = {}
    atomic_execution_unit_ids_by_key: Dict[Union[AssetKey, AssetCheckKey], str] = {}

    for job_def in job_defs:
        asset_layer = job_def.asset_layer
        asset_info_by_node_output = asset_layer.asset_info_by_node_output_handle

        for node_output_handle, asset_info in asset_info_by_node_output.items():
            if not asset_info.is_required:
                continue
            output_key = asset_info.key
            if output_key not in op_names_by_asset_key:
                op_names_by_asset_key[output_key] = [
                    str(handle)
                    for handle in asset_layer.dependency_node_handles_by_asset_key.get(
                        output_key, []
                    )
                ]
            code_version_by_asset_key[output_key] = asset_info.code_version
            upstream_asset_keys = asset_layer.upstream_assets_for_asset(output_key)
            all_upstream_asset_keys.update(upstream_asset_keys)
            node_defs_by_asset_key[output_key].append((node_output_handle, job_def))
            asset_info_by_asset_key[output_key] = asset_info

            for upstream_key in upstream_asset_keys:
                partition_mapping = asset_layer.partition_mapping_for_node_input(
                    node_output_handle.node_handle, upstream_key
                )
                deps[output_key][upstream_key] = ExternalAssetDependency(
                    upstream_asset_key=upstream_key,
                    partition_mapping=(
                        partition_mapping
                        if partition_mapping is None
                        or isinstance(partition_mapping, get_builtin_partition_mapping_types())
                        else None
                    ),
                )
                dep_by[upstream_key][output_key] = ExternalAssetDependedBy(
                    downstream_asset_key=output_key
                )

        for assets_def in asset_layer.assets_defs_by_key.values():
            metadata_by_asset_key.update(assets_def.metadata_by_key)
            freshness_policy_by_asset_key.update(assets_def.freshness_policies_by_key)
            auto_materialize_policy_by_asset_key.update(assets_def.auto_materialize_policies_by_key)
            backfill_policy_by_asset_key.update(
                {key: assets_def.backfill_policy for key in assets_def.keys}
            )
            descriptions_by_asset_key.update(assets_def.descriptions_by_key)
            if len(assets_def.keys) > 1 and not assets_def.can_subset:
                atomic_execution_unit_id = assets_def.unique_id

                for asset_key in assets_def.keys:
                    atomic_execution_unit_ids_by_key[asset_key] = atomic_execution_unit_id
            if len(assets_def.keys) == 1 and assets_def.check_keys and not assets_def.can_subset:
                atomic_execution_unit_ids_by_key[assets_def.key] = assets_def.unique_id

        group_name_by_asset_key.update(asset_layer.group_names_by_assets())

    asset_keys_without_definitions = all_upstream_asset_keys.difference(
        node_defs_by_asset_key.keys()
    ).difference(source_assets_by_key.keys())

    asset_nodes = [
        ExternalAssetNode(
            asset_key=asset_key,
            dependencies=list(deps[asset_key].values()),
            depended_by=list(dep_by[asset_key].values()),
            job_names=[],
            group_name=group_name_by_asset_key.get(asset_key),
            code_version=code_version_by_asset_key.get(asset_key),
        )
        for asset_key in asset_keys_without_definitions
    ]

    for source_asset in source_assets_by_key.values():
        if source_asset.key not in node_defs_by_asset_key:
            job_names = (
                [
                    job_def.name
                    for job_def in job_defs
                    if source_asset.key in job_def.asset_layer.source_assets_by_key
                    and (
                        # explicit source-asset observation job
                        not job_def.asset_layer.has_assets_defs
                        # "base asset job" will have both source and materializable assets
                        or is_base_asset_job_name(job_def.name)
                        and (
                            source_asset.partitions_def is None
                            or source_asset.partitions_def == job_def.partitions_def
                        )
                    )
                ]
                if source_asset.node_def is not None
                else []
            )
            asset_nodes.append(
                ExternalAssetNode(
                    asset_key=source_asset.key,
                    dependencies=list(deps[source_asset.key].values()),
                    depended_by=list(dep_by[source_asset.key].values()),
                    job_names=job_names,
                    op_description=source_asset.description,
                    metadata=source_asset.metadata,
                    group_name=source_asset.group_name,
                    is_source=True,
                    is_observable=source_asset.is_observable,
                    auto_observe_interval_minutes=source_asset.auto_observe_interval_minutes,
                    partitions_def_data=(
                        external_partitions_definition_from_def(source_asset.partitions_def)
                        if source_asset.partitions_def
                        else None
                    ),
                )
            )

    for asset_key, node_tuple_list in node_defs_by_asset_key.items():
        node_output_handle, job_def = node_tuple_list[0]

        node_def = job_def.graph.get_node(node_output_handle.node_handle).definition
        output_def = node_def.output_def_named(node_output_handle.output_name)

        asset_info = asset_info_by_asset_key[asset_key]

        required_top_level_resources: List[str] = []
        if isinstance(node_def, OpDefinition):
            required_top_level_resources = list(node_def.required_resource_keys)

        asset_metadata = (
            normalize_metadata(
                metadata_by_asset_key[asset_key],
                allow_invalid=True,
            )
            if asset_key in metadata_by_asset_key
            else output_def.metadata
        )

        job_names = [job_def.name for _, job_def in node_tuple_list]

        partitions_def_data: Optional[ExternalPartitionsDefinitionData] = None

        partitions_def = asset_info.partitions_def
        if partitions_def:
            partitions_def_data = external_partitions_definition_from_def(partitions_def)

        # if the asset is produced by an op at the top level of the graph, graph_name should be None
        graph_name = None
        node_handle = node_output_handle.node_handle
        while node_handle.parent:
            node_handle = node_handle.parent
            graph_name = node_handle.name

        asset_nodes.append(
            ExternalAssetNode(
                asset_key=asset_key,
                dependencies=list(deps[asset_key].values()),
                depended_by=list(dep_by[asset_key].values()),
                compute_kind=node_def.tags.get("kind"),
                # backcompat
                op_name=graph_name
                or next(iter(op_names_by_asset_key[asset_key]), None)
                or node_def.name,
                graph_name=graph_name,
                op_names=op_names_by_asset_key[asset_key],
                code_version=code_version_by_asset_key.get(asset_key),
                op_description=descriptions_by_asset_key.get(asset_key),
                node_definition_name=node_def.name,
                job_names=job_names,
                partitions_def_data=partitions_def_data,
                output_name=output_def.name,
                metadata=asset_metadata,
                # assets defined by Out(asset_key="k") do not have any group
                # name specified we default to DEFAULT_GROUP_NAME here to ensure
                # such assets are part of the default group
                group_name=group_name_by_asset_key.get(asset_key, DEFAULT_GROUP_NAME),
                freshness_policy=freshness_policy_by_asset_key.get(asset_key),
                auto_materialize_policy=auto_materialize_policy_by_asset_key.get(asset_key),
                backfill_policy=backfill_policy_by_asset_key.get(asset_key),
                atomic_execution_unit_id=atomic_execution_unit_ids_by_key.get(asset_key),
                required_top_level_resources=required_top_level_resources,
            )
        )

    defined = set()
    for node in asset_nodes:
        if node.asset_key in defined:
            check.failed(f"Produced multiple ExternalAssetNodes for key {node.asset_key}")
        else:
            defined.add(node.asset_key)

    return asset_nodes


def external_job_data_from_def(job_def: JobDefinition) -> ExternalJobData:
    check.inst_param(job_def, "job_def", JobDefinition)
    return ExternalJobData(
        name=job_def.name,
        job_snapshot=job_def.get_job_snapshot(),
        parent_job_snapshot=job_def.get_parent_job_snapshot(),
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
        module_name = check.not_none(inspect.getmodule(resource_type_def.resource_fn)).__name__
        resource_type = f"{module_name}.{resource_type_def.resource_fn.__name__}"
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
    else:
        target_dict = {
            target.job_name: ExternalTargetData(
                job_name=target.job_name,
                mode=DEFAULT_MODE_NAME,
                op_selection=target.op_selection,
            )
            for target in sensor_def.targets
        }

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
