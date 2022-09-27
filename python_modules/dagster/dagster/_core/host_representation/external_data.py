"""
This module contains data objects meant to be serialized between
host processes and user processes. They should contain no
business logic or clever indexing. Use the classes in external.py
for that.
"""
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Set, Tuple, Union, cast

import pendulum

from dagster import StaticPartitionsDefinition
from dagster import _check as check
from dagster._core.definitions import (
    JobDefinition,
    PartitionSetDefinition,
    PartitionsDefinition,
    PipelineDefinition,
    PresetDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
    SourceAsset,
)
from dagster._core.definitions.asset_layer import AssetOutputInfo
from dagster._core.definitions.dependency import NodeOutputHandle
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.metadata import MetadataEntry, MetadataUserInput, normalize_metadata
from dagster._core.definitions.mode import DEFAULT_MODE_NAME
from dagster._core.definitions.partition import PartitionScheduleDefinition, ScheduleType
from dagster._core.definitions.schedule_definition import DefaultScheduleStatus
from dagster._core.definitions.sensor_definition import (
    AssetSensorDefinition,
    DefaultSensorStatus,
    SensorDefinition,
)
from dagster._core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster._core.definitions.utils import DEFAULT_GROUP_NAME
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster._core.snap import PipelineSnapshot
from dagster._serdes import DefaultNamedTupleSerializer, whitelist_for_serdes
from dagster._utils.error import SerializableErrorInfo


@whitelist_for_serdes
class ExternalRepositoryData(
    NamedTuple(
        "_ExternalRepositoryData",
        [
            ("name", str),
            ("external_schedule_datas", Sequence["ExternalScheduleData"]),
            ("external_partition_set_datas", Sequence["ExternalPartitionSetData"]),
            ("external_sensor_datas", Sequence["ExternalSensorData"]),
            ("external_asset_graph_data", Sequence["ExternalAssetNode"]),
            ("external_pipeline_datas", Optional[Sequence["ExternalPipelineData"]]),
            ("external_job_refs", Optional[Sequence["ExternalJobRef"]]),
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
        external_pipeline_datas: Optional[Sequence["ExternalPipelineData"]] = None,
        external_job_refs: Optional[Sequence["ExternalJobRef"]] = None,
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
            external_pipeline_datas=check.opt_nullable_sequence_param(
                external_pipeline_datas, "external_pipeline_datas", of_type=ExternalPipelineData
            ),
            external_job_refs=check.opt_nullable_sequence_param(
                external_job_refs, "external_job_refs", of_type=ExternalJobRef
            ),
        )

    def has_pipeline_data(self):
        return self.external_pipeline_datas is not None

    def get_external_pipeline_datas(self) -> Sequence["ExternalPipelineData"]:
        if self.external_pipeline_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")
        return self.external_pipeline_datas

    def get_external_job_refs(self) -> Sequence["ExternalJobRef"]:
        if self.external_job_refs is None:
            check.failed("Snapshots were not deferred, external_job_refs not loaded")
        return self.external_job_refs

    def get_pipeline_snapshot(self, name):
        check.str_param(name, "name")
        if self.external_pipeline_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data.pipeline_snapshot

        check.failed("Could not find pipeline snapshot named " + name)

    def get_external_pipeline_data(self, name):
        check.str_param(name, "name")
        if self.external_pipeline_datas is None:
            check.failed("Snapshots were deferred, external_pipeline_data not loaded")

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data

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


@whitelist_for_serdes
class ExternalPipelineSubsetResult(
    NamedTuple(
        "_ExternalPipelineSubsetResult",
        [
            ("success", bool),
            ("error", Optional[SerializableErrorInfo]),
            ("external_pipeline_data", Optional["ExternalPipelineData"]),
        ],
    )
):
    def __new__(
        cls,
        success: bool,
        error: Optional[SerializableErrorInfo] = None,
        external_pipeline_data: Optional["ExternalPipelineData"] = None,
    ):
        return super(ExternalPipelineSubsetResult, cls).__new__(
            cls,
            success=check.bool_param(success, "success"),
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
            external_pipeline_data=check.opt_inst_param(
                external_pipeline_data, "external_pipeline_data", ExternalPipelineData
            ),
        )


@whitelist_for_serdes
class ExternalPipelineData(
    NamedTuple(
        "_ExternalPipelineData",
        [
            ("name", str),
            ("pipeline_snapshot", PipelineSnapshot),
            ("active_presets", Sequence["ExternalPresetData"]),
            ("parent_pipeline_snapshot", Optional[PipelineSnapshot]),
            ("is_job", bool),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        pipeline_snapshot: PipelineSnapshot,
        active_presets: Sequence["ExternalPresetData"],
        parent_pipeline_snapshot: Optional[PipelineSnapshot],
        is_job: bool = False,
    ):
        return super(ExternalPipelineData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            pipeline_snapshot=check.inst_param(
                pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot
            ),
            parent_pipeline_snapshot=check.opt_inst_param(
                parent_pipeline_snapshot, "parent_pipeline_snapshot", PipelineSnapshot
            ),
            active_presets=check.list_param(
                active_presets, "active_presets", of_type=ExternalPresetData
            ),
            is_job=check.bool_param(is_job, "is_job"),
        )


@whitelist_for_serdes
class ExternalJobRef(
    NamedTuple(
        "_ExternalJobRef",
        [
            ("name", str),
            ("snapshot_id", str),
            ("active_presets", Sequence["ExternalPresetData"]),
            ("parent_snapshot_id", Optional[str]),
            ("is_legacy_pipeline", bool),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        snapshot_id: str,
        active_presets: Sequence["ExternalPresetData"],
        parent_snapshot_id: Optional[str],
        is_legacy_pipeline: bool = False,
    ):
        return super(ExternalJobRef, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            snapshot_id=check.str_param(snapshot_id, "snapshot_id"),
            active_presets=check.list_param(
                active_presets, "active_presets", of_type=ExternalPresetData
            ),
            parent_snapshot_id=check.opt_str_param(parent_snapshot_id, "parent_snapshot_id"),
            is_legacy_pipeline=check.bool_param(is_legacy_pipeline, "is_legacy"),
        )


@whitelist_for_serdes
class ExternalPresetData(
    NamedTuple(
        "_ExternalPresetData",
        [
            ("name", str),
            ("run_config", Mapping[str, object]),
            ("solid_selection", Optional[Sequence[str]]),
            ("mode", str),
            ("tags", Mapping[str, str]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        run_config: Optional[Mapping[str, object]],
        solid_selection: Optional[Sequence[str]],
        mode: str,
        tags: Mapping[str, str],
    ):
        return super(ExternalPresetData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            run_config=check.opt_mapping_param(run_config, "run_config", key_type=str),
            solid_selection=check.opt_nullable_sequence_param(
                solid_selection, "solid_selection", of_type=str
            ),
            mode=check.str_param(mode, "mode"),
            tags=check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
        )


class ExternalScheduleDataSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def skip_when_empty(cls) -> Set[str]:
        return {"default_status"}  # Maintain stable snapshot ID for back-compat purposes


@whitelist_for_serdes(serializer=ExternalScheduleDataSerializer)
class ExternalScheduleData(
    NamedTuple(
        "_ExternalScheduleData",
        [
            ("name", str),
            ("cron_schedule", Union[str, Sequence[str]]),
            ("pipeline_name", str),
            ("solid_selection", Optional[Sequence[str]]),
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
        pipeline_name,
        solid_selection,
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
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
            mode=check.opt_str_param(mode, "mode"),
            environment_vars=check.opt_dict_param(environment_vars, "environment_vars"),
            partition_set_name=check.opt_str_param(partition_set_name, "partition_set_name"),
            execution_timezone=check.opt_str_param(execution_timezone, "execution_timezone"),
            description=check.opt_str_param(description, "description"),
            # Leave default_status as None if it's STOPPED to maintain stable back-compat IDs
            default_status=DefaultScheduleStatus.RUNNING
            if default_status == DefaultScheduleStatus.RUNNING
            else None,
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


@whitelist_for_serdes
class ExternalTargetData(
    NamedTuple(
        "_ExternalTargetData",
        [("pipeline_name", str), ("mode", str), ("solid_selection", Optional[Sequence[str]])],
    )
):
    def __new__(cls, pipeline_name: str, mode: str, solid_selection: Optional[Sequence[str]]):
        return super(ExternalTargetData, cls).__new__(
            cls,
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            mode=check.str_param(mode, "mode"),
            solid_selection=check.opt_nullable_sequence_param(
                solid_selection, "solid_selection", str
            ),
        )


@whitelist_for_serdes
class ExternalSensorMetadata(
    NamedTuple("_ExternalSensorMetadata", [("asset_keys", Optional[Sequence[AssetKey]])])
):
    """Stores additional sensor metadata which is available on the Dagit frontend."""

    def __new__(cls, asset_keys: Optional[Sequence[AssetKey]] = None):
        return super(ExternalSensorMetadata, cls).__new__(
            cls,
            asset_keys=check.opt_nullable_sequence_param(
                asset_keys, "asset_keys", of_type=AssetKey
            ),
        )


class ExternalSensorDataSerializer(DefaultNamedTupleSerializer):
    @classmethod
    def skip_when_empty(cls) -> Set[str]:
        return {"default_status"}  # Maintain stable snapshot ID for back-compat purposes


@whitelist_for_serdes(serializer=ExternalSensorDataSerializer)
class ExternalSensorData(
    NamedTuple(
        "_ExternalSensorData",
        [
            ("name", str),
            ("pipeline_name", Optional[str]),
            ("solid_selection", Optional[Sequence[str]]),
            ("mode", Optional[str]),
            ("min_interval", Optional[int]),
            ("description", Optional[str]),
            ("target_dict", Mapping[str, ExternalTargetData]),
            ("metadata", Optional[ExternalSensorMetadata]),
            ("default_status", Optional[DefaultSensorStatus]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        pipeline_name: Optional[str] = None,
        solid_selection: Optional[Sequence[str]] = None,
        mode: Optional[str] = None,
        min_interval: Optional[int] = None,
        description: Optional[str] = None,
        target_dict: Optional[Mapping[str, ExternalTargetData]] = None,
        metadata: Optional[ExternalSensorMetadata] = None,
        default_status: Optional[DefaultSensorStatus] = None,
    ):
        if pipeline_name and not target_dict:
            # handle the legacy case where the ExternalSensorData was constructed from an earlier
            # version of dagster
            target_dict = {
                pipeline_name: ExternalTargetData(
                    pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
                    mode=check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME),
                    solid_selection=check.opt_nullable_sequence_param(
                        solid_selection, "solid_selection", str
                    ),
                )
            }

        return super(ExternalSensorData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            pipeline_name=check.opt_str_param(
                pipeline_name, "pipeline_name"
            ),  # keep legacy field populated
            solid_selection=check.opt_nullable_sequence_param(
                solid_selection, "solid_selection", str
            ),  # keep legacy field populated
            mode=check.opt_str_param(mode, "mode"),  # keep legacy field populated
            min_interval=check.opt_int_param(min_interval, "min_interval"),
            description=check.opt_str_param(description, "description"),
            target_dict=check.opt_dict_param(target_dict, "target_dict", str, ExternalTargetData),
            metadata=check.opt_inst_param(metadata, "metadata", ExternalSensorMetadata),
            default_status=DefaultSensorStatus.RUNNING
            if default_status == DefaultSensorStatus.RUNNING
            else None,
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
    def get_partitions_definition(self) -> PartitionsDefinition:
        ...


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
            )
        else:
            # backcompat case
            return TimeWindowPartitionsDefinition(
                schedule_type=self.schedule_type,
                start=pendulum.from_timestamp(self.start, tz=self.timezone),
                timezone=self.timezone,
                fmt=self.fmt,
                end_offset=self.end_offset,
                minute_offset=self.minute_offset,
                hour_offset=self.hour_offset,
                day_offset=self.day_offset,
            )


@whitelist_for_serdes
class ExternalStaticPartitionsDefinitionData(
    ExternalPartitionsDefinitionData,
    NamedTuple("_ExternalStaticPartitionsDefinitionData", [("partition_keys", Sequence[str])]),
):
    def __new__(cls, partition_keys: Sequence[str]):
        return super(ExternalStaticPartitionsDefinitionData, cls).__new__(
            cls, partition_keys=check.list_param(partition_keys, "partition_keys", str)
        )

    def get_partitions_definition(self):
        return StaticPartitionsDefinition(self.partition_keys)


@whitelist_for_serdes
class ExternalPartitionSetData(
    NamedTuple(
        "_ExternalPartitionSetData",
        [
            ("name", str),
            ("pipeline_name", str),
            ("solid_selection", Optional[Sequence[str]]),
            ("mode", Optional[str]),
            ("external_partitions_data", Optional[ExternalPartitionsDefinitionData]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        pipeline_name: str,
        solid_selection: Optional[Sequence[str]],
        mode: Optional[str],
        external_partitions_data: Optional[ExternalPartitionsDefinitionData] = None,
    ):
        return super(ExternalPartitionSetData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_sequence_param(
                solid_selection, "solid_selection", str
            ),
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
            partition_names=check.opt_list_param(partition_names, "partition_names", str),
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
    def __new__(cls, name: str, tags: Optional[Mapping[str, object]] = None):
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
    def __new__(cls, name: str, tags: Mapping[str, object], run_config: Mapping[str, object]):
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
            partition_data=check.list_param(
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
    ):
        return super(ExternalAssetDependency, cls).__new__(
            cls,
            upstream_asset_key=upstream_asset_key,
            input_name=input_name,
            output_name=output_name,
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
            ("node_definition_name", Optional[str]),
            ("graph_name", Optional[str]),
            ("op_description", Optional[str]),
            ("job_names", Sequence[str]),
            ("partitions_def_data", Optional[ExternalPartitionsDefinitionData]),
            ("output_name", Optional[str]),
            ("output_description", Optional[str]),
            ("metadata_entries", Sequence[MetadataEntry]),
            ("group_name", Optional[str]),
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
        node_definition_name: Optional[str] = None,
        graph_name: Optional[str] = None,
        op_description: Optional[str] = None,
        job_names: Optional[Sequence[str]] = None,
        partitions_def_data: Optional[ExternalPartitionsDefinitionData] = None,
        output_name: Optional[str] = None,
        output_description: Optional[str] = None,
        metadata_entries: Optional[Sequence[MetadataEntry]] = None,
        group_name: Optional[str] = None,
    ):
        # backcompat logic to handle ExternalAssetNodes serialized without op_names/graph_name
        if not op_names:
            op_names = list(filter(None, [op_name]))
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
            op_names=check.opt_list_param(op_names, "op_names"),
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
            metadata_entries=check.opt_sequence_param(
                metadata_entries, "metadata_entries", of_type=MetadataEntry
            ),
            group_name=check.opt_str_param(group_name, "group_name"),
        )


def external_repository_data_from_def(
    repository_def: RepositoryDefinition,
    defer_snapshots: bool = False,
) -> ExternalRepositoryData:
    check.inst_param(repository_def, "repository_def", RepositoryDefinition)

    pipelines = repository_def.get_all_pipelines()
    if defer_snapshots:
        pipeline_datas = None
        job_refs = sorted(
            list(map(external_job_ref_from_def, pipelines)),
            key=lambda pd: pd.name,
        )
    else:
        pipeline_datas = sorted(
            list(map(external_pipeline_data_from_def, pipelines)),
            key=lambda pd: pd.name,
        )
        job_refs = None

    return ExternalRepositoryData(
        name=repository_def.name,
        external_schedule_datas=sorted(
            list(map(external_schedule_data_from_def, repository_def.schedule_defs)),
            key=lambda sd: sd.name,
        ),
        external_partition_set_datas=sorted(
            list(map(external_partition_set_data_from_def, repository_def.partition_set_defs)),
            key=lambda psd: psd.name,
        ),
        external_sensor_datas=sorted(
            list(map(external_sensor_data_from_def, repository_def.sensor_defs)),
            key=lambda sd: sd.name,
        ),
        external_asset_graph_data=external_asset_graph_from_defs(
            pipelines, source_assets_by_key=repository_def.source_assets_by_key
        ),
        external_pipeline_datas=pipeline_datas,
        external_job_refs=job_refs,
    )


def external_asset_graph_from_defs(
    pipelines: Sequence[PipelineDefinition], source_assets_by_key: Mapping[AssetKey, SourceAsset]
) -> Sequence[ExternalAssetNode]:
    node_defs_by_asset_key: Dict[
        AssetKey, List[Tuple[NodeOutputHandle, PipelineDefinition]]
    ] = defaultdict(list)
    asset_info_by_asset_key: Dict[AssetKey, AssetOutputInfo] = dict()
    metadata_by_asset_key: Dict[AssetKey, MetadataUserInput] = dict()

    deps: Dict[AssetKey, Dict[AssetKey, ExternalAssetDependency]] = defaultdict(dict)
    dep_by: Dict[AssetKey, Dict[AssetKey, ExternalAssetDependedBy]] = defaultdict(dict)
    all_upstream_asset_keys: Set[AssetKey] = set()
    op_names_by_asset_key: Dict[AssetKey, Sequence[str]] = {}
    group_names: Dict[AssetKey, str] = {}

    for pipeline_def in pipelines:
        asset_info_by_node_output = pipeline_def.asset_layer.asset_info_by_node_output_handle

        for node_output_handle, asset_info in asset_info_by_node_output.items():
            if not asset_info.is_required:
                continue
            output_key = asset_info.key
            if output_key not in op_names_by_asset_key:
                op_names_by_asset_key[output_key] = [
                    str(handle)
                    for handle in pipeline_def.asset_layer.dependency_node_handles_by_asset_key.get(
                        output_key, []
                    )
                ]
            upstream_asset_keys = pipeline_def.asset_layer.upstream_assets_for_asset(output_key)
            all_upstream_asset_keys.update(upstream_asset_keys)
            node_defs_by_asset_key[output_key].append((node_output_handle, pipeline_def))
            asset_info_by_asset_key[output_key] = asset_info

            for upstream_key in upstream_asset_keys:
                deps[output_key][upstream_key] = ExternalAssetDependency(
                    upstream_asset_key=upstream_key
                )
                dep_by[upstream_key][output_key] = ExternalAssetDependedBy(
                    downstream_asset_key=output_key
                )

        for assets_def in pipeline_def.asset_layer.assets_defs_by_key.values():
            metadata_by_asset_key.update(assets_def.metadata_by_key)
        group_names.update(pipeline_def.asset_layer.group_names_by_assets())

    asset_keys_without_definitions = all_upstream_asset_keys.difference(
        node_defs_by_asset_key.keys()
    ).difference(source_assets_by_key.keys())

    asset_nodes = [
        ExternalAssetNode(
            asset_key=asset_key,
            dependencies=list(deps[asset_key].values()),
            depended_by=list(dep_by[asset_key].values()),
            job_names=[],
            group_name=group_names.get(asset_key),
        )
        for asset_key in asset_keys_without_definitions
    ]

    for source_asset in source_assets_by_key.values():
        if source_asset.key not in node_defs_by_asset_key:
            # TODO: For now we are dropping partition metadata entries
            metadata_entries = [
                entry for entry in source_asset.metadata_entries if isinstance(entry, MetadataEntry)
            ]
            asset_nodes.append(
                ExternalAssetNode(
                    asset_key=source_asset.key,
                    dependencies=list(deps[source_asset.key].values()),
                    depended_by=list(dep_by[source_asset.key].values()),
                    job_names=[],
                    op_description=source_asset.description,
                    metadata_entries=metadata_entries,
                    group_name=source_asset.group_name,
                )
            )

    for asset_key, node_tuple_list in node_defs_by_asset_key.items():
        node_output_handle, job_def = node_tuple_list[0]

        node_def = job_def.graph.get_solid(node_output_handle.node_handle).definition
        output_def = node_def.output_def_named(node_output_handle.output_name)

        asset_info = asset_info_by_asset_key[asset_key]

        asset_metadata_entries = (
            cast(
                Sequence,
                normalize_metadata(
                    metadata=metadata_by_asset_key[asset_key],
                    metadata_entries=[],
                    allow_invalid=True,
                ),
            )
            if asset_key in metadata_by_asset_key
            else cast(Sequence, output_def.metadata_entries)
        )

        job_names = [job_def.name for _, job_def in node_tuple_list]

        # temporary workaround to retrieve asset partition definition from job
        partitions_def_data: Optional[
            Union[
                ExternalTimeWindowPartitionsDefinitionData,
                ExternalStaticPartitionsDefinitionData,
            ]
        ] = None

        partitions_def = asset_info.partitions_def
        if partitions_def:
            if isinstance(partitions_def, TimeWindowPartitionsDefinition):
                partitions_def_data = external_time_window_partitions_definition_from_def(
                    partitions_def
                )
            elif isinstance(partitions_def, StaticPartitionsDefinition):
                partitions_def_data = external_static_partitions_definition_from_def(partitions_def)
            else:
                raise DagsterInvalidDefinitionError(
                    "Only static partition and time window partitions are currently supported."
                )

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
                op_description=node_def.description or output_def.description,
                node_definition_name=node_def.name,
                job_names=job_names,
                partitions_def_data=partitions_def_data,
                output_name=output_def.name,
                metadata_entries=asset_metadata_entries,
                # assets defined by Out(asset_key="k") do not have any group
                # name specified we default to DEFAULT_GROUP_NAME here to ensure
                # such assets are part of the default group
                group_name=group_names.get(asset_key, DEFAULT_GROUP_NAME),
            )
        )

    return asset_nodes


def external_pipeline_data_from_def(pipeline_def: PipelineDefinition) -> ExternalPipelineData:
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    return ExternalPipelineData(
        name=pipeline_def.name,
        pipeline_snapshot=pipeline_def.get_pipeline_snapshot(),
        parent_pipeline_snapshot=pipeline_def.get_parent_pipeline_snapshot(),
        active_presets=sorted(
            list(map(external_preset_data_from_def, pipeline_def.preset_defs)),
            key=lambda pd: pd.name,
        ),
        is_job=isinstance(pipeline_def, JobDefinition),
    )


def external_job_ref_from_def(pipeline_def: PipelineDefinition) -> ExternalJobRef:
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)

    parent = pipeline_def.parent_pipeline_def
    if parent:
        parent_snapshot_id = parent.get_pipeline_snapshot_id()
    else:
        parent_snapshot_id = None

    return ExternalJobRef(
        name=pipeline_def.name,
        snapshot_id=pipeline_def.get_pipeline_snapshot_id(),
        parent_snapshot_id=parent_snapshot_id,
        active_presets=sorted(
            list(map(external_preset_data_from_def, pipeline_def.preset_defs)),
            key=lambda pd: pd.name,
        ),
        is_legacy_pipeline=not isinstance(pipeline_def, JobDefinition),
    )


def external_schedule_data_from_def(schedule_def: ScheduleDefinition) -> ExternalScheduleData:
    check.inst_param(schedule_def, "schedule_def", ScheduleDefinition)
    return ExternalScheduleData(
        name=schedule_def.name,
        cron_schedule=schedule_def.cron_schedule,
        pipeline_name=schedule_def.job_name,
        solid_selection=schedule_def._target.solid_selection,  # pylint: disable=protected-access
        mode=schedule_def._target.mode,  # pylint: disable=protected-access
        environment_vars=schedule_def.environment_vars,
        partition_set_name=schedule_def.get_partition_set().name
        if isinstance(schedule_def, PartitionScheduleDefinition)
        else None,
        execution_timezone=schedule_def.execution_timezone,
        description=schedule_def.description,
        default_status=schedule_def.default_status,
    )


def external_time_window_partitions_definition_from_def(
    partitions_def: TimeWindowPartitionsDefinition,
) -> ExternalTimeWindowPartitionsDefinitionData:
    check.inst_param(partitions_def, "partitions_def", TimeWindowPartitionsDefinition)
    return ExternalTimeWindowPartitionsDefinitionData(
        cron_schedule=partitions_def.cron_schedule,
        start=pendulum.instance(partitions_def.start, tz=partitions_def.timezone).timestamp(),
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


def external_partition_set_data_from_def(
    partition_set_def: PartitionSetDefinition,
) -> ExternalPartitionSetData:
    check.inst_param(partition_set_def, "partition_set_def", PartitionSetDefinition)

    partitions_def = partition_set_def._partitions_def  # pylint: disable=protected-access

    partitions_def_data: Optional[ExternalPartitionsDefinitionData] = None
    if isinstance(partitions_def, TimeWindowPartitionsDefinition):
        partitions_def_data = external_time_window_partitions_definition_from_def(partitions_def)
    elif isinstance(partitions_def, StaticPartitionsDefinition):
        partitions_def_data = external_static_partitions_definition_from_def(partitions_def)
    else:
        partitions_def_data = None

    return ExternalPartitionSetData(
        name=partition_set_def.name,
        pipeline_name=partition_set_def.pipeline_or_job_name,
        solid_selection=partition_set_def.solid_selection,
        mode=partition_set_def.mode,
        external_partitions_data=partitions_def_data,
    )


def external_sensor_data_from_def(sensor_def: SensorDefinition) -> ExternalSensorData:
    first_target = sensor_def.targets[0] if sensor_def.targets else None

    asset_keys = None
    if isinstance(sensor_def, AssetSensorDefinition):
        asset_keys = [sensor_def.asset_key]

    return ExternalSensorData(
        name=sensor_def.name,
        pipeline_name=first_target.pipeline_name if first_target else None,
        mode=first_target.mode if first_target else None,
        solid_selection=first_target.solid_selection if first_target else None,
        target_dict={
            target.pipeline_name: ExternalTargetData(
                pipeline_name=target.pipeline_name,
                mode=target.mode,
                solid_selection=target.solid_selection,
            )
            for target in sensor_def.targets
        },
        min_interval=sensor_def.minimum_interval_seconds,
        description=sensor_def.description,
        metadata=ExternalSensorMetadata(asset_keys=asset_keys),
        default_status=sensor_def.default_status,
    )


def external_preset_data_from_def(preset_def: PresetDefinition) -> ExternalPresetData:
    check.inst_param(preset_def, "preset_def", PresetDefinition)
    return ExternalPresetData(
        name=preset_def.name,
        run_config=preset_def.run_config,
        solid_selection=preset_def.solid_selection,
        mode=preset_def.mode,
        tags=preset_def.tags,
    )
