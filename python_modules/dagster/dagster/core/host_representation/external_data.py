"""
This module contains data objects meant to be serialized between
host processes and user processes. They should contain no
business logic or clever indexing. Use the classes in external.py
for that.
"""
from abc import ABC, abstractmethod
from collections import defaultdict, namedtuple
from datetime import datetime
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

from dagster import StaticPartitionsDefinition, check
from dagster.core.asset_defs import ForeignAsset
from dagster.core.definitions import (
    JobDefinition,
    OutputDefinition,
    PartitionSetDefinition,
    PartitionsDefinition,
    PipelineDefinition,
    PresetDefinition,
    RepositoryDefinition,
    ScheduleDefinition,
)
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.mode import DEFAULT_MODE_NAME
from dagster.core.definitions.node_definition import NodeDefinition
from dagster.core.definitions.partition import PartitionScheduleDefinition, ScheduleType
from dagster.core.definitions.sensor_definition import AssetSensorDefinition
from dagster.core.definitions.time_window_partitions import TimeWindowPartitionsDefinition
from dagster.core.errors import DagsterInvalidDefinitionError, DagsterInvariantViolationError
from dagster.core.snap import PipelineSnapshot
from dagster.serdes import whitelist_for_serdes
from dagster.utils.error import SerializableErrorInfo


@whitelist_for_serdes
class ExternalRepositoryData(
    namedtuple(
        "_ExternalRepositoryData",
        "name external_pipeline_datas external_schedule_datas external_partition_set_datas external_sensor_datas external_asset_graph_data",
    )
):
    def __new__(
        cls,
        name,
        external_pipeline_datas,
        external_schedule_datas,
        external_partition_set_datas,
        external_sensor_datas=None,
        external_asset_graph_data=None,
    ):
        return super(ExternalRepositoryData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            external_pipeline_datas=check.list_param(
                external_pipeline_datas, "external_pipeline_datas", of_type=ExternalPipelineData
            ),
            external_schedule_datas=check.list_param(
                external_schedule_datas, "external_schedule_datas", of_type=ExternalScheduleData
            ),
            external_partition_set_datas=check.list_param(
                external_partition_set_datas,
                "external_partition_set_datas",
                of_type=ExternalPartitionSetData,
            ),
            external_sensor_datas=check.opt_list_param(
                external_sensor_datas,
                "external_sensor_datas",
                of_type=ExternalSensorData,
            ),
            external_asset_graph_data=check.opt_list_param(
                external_asset_graph_data,
                "external_asset_graph_dats",
                of_type=ExternalAssetNode,
            ),
        )

    def get_pipeline_snapshot(self, name):
        check.str_param(name, "name")

        for external_pipeline_data in self.external_pipeline_datas:
            if external_pipeline_data.name == name:
                return external_pipeline_data.pipeline_snapshot

        check.failed("Could not find pipeline snapshot named " + name)

    def get_external_pipeline_data(self, name):
        check.str_param(name, "name")

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
    namedtuple("_ExternalPipelineSubsetResult", "success error external_pipeline_data")
):
    def __new__(cls, success, error=None, external_pipeline_data=None):
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
    namedtuple(
        "_ExternalPipelineData",
        "name pipeline_snapshot active_presets parent_pipeline_snapshot is_job",
    )
):
    def __new__(
        cls, name, pipeline_snapshot, active_presets, parent_pipeline_snapshot, is_job=False
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
class ExternalPresetData(
    namedtuple("_ExternalPresetData", "name run_config solid_selection mode tags")
):
    def __new__(cls, name, run_config, solid_selection, mode, tags):
        return super(ExternalPresetData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            run_config=check.opt_dict_param(run_config, "run_config"),
            solid_selection=check.opt_nullable_list_param(
                solid_selection, "solid_selection", of_type=str
            ),
            mode=check.str_param(mode, "mode"),
            tags=check.opt_dict_param(tags, "tags"),
        )


@whitelist_for_serdes
class ExternalScheduleData(
    namedtuple(
        "_ExternalScheduleData",
        "name cron_schedule pipeline_name solid_selection mode environment_vars partition_set_name execution_timezone description",
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
    ):
        return super(ExternalScheduleData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            cron_schedule=check.str_param(cron_schedule, "cron_schedule"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
            mode=check.opt_str_param(mode, "mode"),
            environment_vars=check.opt_dict_param(environment_vars, "environment_vars"),
            partition_set_name=check.opt_str_param(partition_set_name, "partition_set_name"),
            execution_timezone=check.opt_str_param(execution_timezone, "execution_timezone"),
            description=check.opt_str_param(description, "description"),
        )


@whitelist_for_serdes
class ExternalScheduleExecutionErrorData(
    namedtuple("_ExternalScheduleExecutionErrorData", "error")
):
    def __new__(cls, error):
        return super(ExternalScheduleExecutionErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalTargetData(
    namedtuple(
        "_ExternalTargetData",
        "pipeline_name mode solid_selection",
    )
):
    def __new__(
        cls,
        pipeline_name,
        mode,
        solid_selection,
    ):
        return super(ExternalTargetData, cls).__new__(
            cls,
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            mode=check.str_param(mode, "mode"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
        )


@whitelist_for_serdes
class ExternalSensorMetadata(namedtuple("_ExternalSensorMetadata", "asset_keys")):
    """Stores additional sensor metadata which is available on the Dagit frontend."""

    def __new__(cls, asset_keys=None):
        return super(ExternalSensorMetadata, cls).__new__(
            cls, asset_keys=check.opt_nullable_list_param(asset_keys, "asset_keys")
        )


@whitelist_for_serdes
class ExternalSensorData(
    namedtuple(
        "_ExternalSensorData",
        "name pipeline_name solid_selection mode min_interval description target_dict metadata",
    )
):
    def __new__(
        cls,
        name,
        pipeline_name=None,
        solid_selection=None,
        mode=None,
        min_interval=None,
        description=None,
        target_dict=None,
        metadata=None,
    ):
        if pipeline_name and not target_dict:
            # handle the legacy case where the ExternalSensorData was constructed from an earlier
            # version of dagster
            target_dict = {
                pipeline_name: ExternalTargetData(
                    pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
                    mode=check.opt_str_param(mode, "mode", DEFAULT_MODE_NAME),
                    solid_selection=check.opt_nullable_list_param(
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
            solid_selection=check.opt_nullable_list_param(
                solid_selection, "solid_selection", str
            ),  # keep legacy field populated
            mode=check.opt_str_param(mode, "mode"),  # keep legacy field populated
            min_interval=check.opt_int_param(min_interval, "min_interval"),
            description=check.opt_str_param(description, "description"),
            target_dict=check.opt_dict_param(target_dict, "target_dict", str, ExternalTargetData),
            metadata=check.opt_inst_param(metadata, "metadata", ExternalSensorMetadata),
        )


@whitelist_for_serdes
class ExternalSensorExecutionErrorData(namedtuple("_ExternalSensorExecutionErrorData", "error")):
    def __new__(cls, error):
        return super(ExternalSensorExecutionErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalExecutionParamsData(namedtuple("_ExternalExecutionParamsData", "run_config tags")):
    def __new__(cls, run_config=None, tags=None):
        return super(ExternalExecutionParamsData, cls).__new__(
            cls,
            run_config=check.opt_dict_param(run_config, "run_config"),
            tags=check.opt_dict_param(tags, "tags", key_type=str, value_type=str),
        )


@whitelist_for_serdes
class ExternalExecutionParamsErrorData(namedtuple("_ExternalExecutionParamsErrorData", "error")):
    def __new__(cls, error):
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
    namedtuple(
        "_ExternalTimeWindowPartitionsDefinitionData", "schedule_type start timezone fmt end_offset"
    ),
):
    def __new__(cls, schedule_type, start, timezone, fmt, end_offset):
        return super(ExternalTimeWindowPartitionsDefinitionData, cls).__new__(
            cls,
            schedule_type=check.inst_param(schedule_type, "schedule_type", ScheduleType),
            start=check.float_param(start, "start"),
            timezone=check.opt_str_param(timezone, "timezone"),
            fmt=check.str_param(fmt, "fmt"),
            end_offset=check.int_param(end_offset, "end_offset"),
        )

    def get_partitions_definition(self):
        return TimeWindowPartitionsDefinition(
            self.schedule_type,
            datetime.fromtimestamp(self.start),
            self.timezone,
            self.fmt,
            self.end_offset,
        )


@whitelist_for_serdes
class ExternalStaticPartitionsDefinitionData(
    ExternalPartitionsDefinitionData,
    namedtuple("_ExternalStaticPartitionsDefinitionData", "partition_keys"),
):
    def __new__(cls, partition_keys):
        return super(ExternalStaticPartitionsDefinitionData, cls).__new__(
            cls, partition_keys=check.list_param(partition_keys, "partition_keys", str)
        )

    def get_partitions_definition(self):
        return StaticPartitionsDefinition(self.partition_keys)


@whitelist_for_serdes
class ExternalPartitionSetData(
    namedtuple("_ExternalPartitionSetData", "name pipeline_name solid_selection mode")
):
    def __new__(cls, name, pipeline_name, solid_selection, mode):
        return super(ExternalPartitionSetData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            pipeline_name=check.str_param(pipeline_name, "pipeline_name"),
            solid_selection=check.opt_nullable_list_param(solid_selection, "solid_selection", str),
            mode=check.opt_str_param(mode, "mode"),
        )


@whitelist_for_serdes
class ExternalPartitionNamesData(namedtuple("_ExternalPartitionNamesData", "partition_names")):
    def __new__(cls, partition_names=None):
        return super(ExternalPartitionNamesData, cls).__new__(
            cls,
            partition_names=check.opt_list_param(partition_names, "partition_names", str),
        )


@whitelist_for_serdes
class ExternalPartitionConfigData(namedtuple("_ExternalPartitionConfigData", "name run_config")):
    def __new__(cls, name, run_config=None):
        return super(ExternalPartitionConfigData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            run_config=check.opt_dict_param(run_config, "run_config"),
        )


@whitelist_for_serdes
class ExternalPartitionTagsData(namedtuple("_ExternalPartitionTagsData", "name tags")):
    def __new__(cls, name, tags=None):
        return super(ExternalPartitionTagsData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            tags=check.opt_dict_param(tags, "tags"),
        )


@whitelist_for_serdes
class ExternalPartitionExecutionParamData(
    namedtuple("_ExternalPartitionExecutionParamData", "name tags run_config")
):
    def __new__(cls, name, tags, run_config):
        return super(ExternalPartitionExecutionParamData, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            tags=check.dict_param(tags, "tags"),
            run_config=check.opt_dict_param(run_config, "run_config"),
        )


@whitelist_for_serdes
class ExternalPartitionSetExecutionParamData(
    namedtuple("_ExternalPartitionSetExecutionParamData", "partition_data")
):
    def __new__(cls, partition_data):
        return super(ExternalPartitionSetExecutionParamData, cls).__new__(
            cls,
            partition_data=check.list_param(
                partition_data, "partition_data", of_type=ExternalPartitionExecutionParamData
            ),
        )


@whitelist_for_serdes
class ExternalPartitionExecutionErrorData(
    namedtuple("_ExternalPartitionExecutionErrorData", "error")
):
    def __new__(cls, error):
        return super(ExternalPartitionExecutionErrorData, cls).__new__(
            cls,
            error=check.opt_inst_param(error, "error", SerializableErrorInfo),
        )


@whitelist_for_serdes
class ExternalAssetDependency(
    namedtuple("_ExternalAssetDependency", "upstream_asset_key input_name output_name")
):
    """A definition of a directed edge in the logical asset graph.

    An upstream asset that's depended on, and the corresponding input name in the downstream asset
    that depends on it.
    """

    def __new__(cls, upstream_asset_key: AssetKey, input_name: str = None, output_name: str = None):
        check.invariant(
            (input_name is None) ^ (output_name is None),
            "Exactly one of `input_name` and `output_name` should be supplied",
        )
        return super(ExternalAssetDependency, cls).__new__(
            cls,
            upstream_asset_key=upstream_asset_key,
            input_name=input_name,
            output_name=output_name,
        )


@whitelist_for_serdes
class ExternalAssetDependedBy(
    namedtuple("_ExternalAssetDependedBy", "downstream_asset_key input_name output_name")
):
    """A definition of a directed edge in the logical asset graph.

    An downstream asset that's depended by, and the corresponding input name in the upstream
    asset that it depends on.
    """

    def __new__(
        cls, downstream_asset_key: AssetKey, input_name: str = None, output_name: str = None
    ):
        check.invariant(
            (input_name is None) ^ (output_name is None),
            "Exactly one of `input_name` and `output_name` should be supplied",
        )
        return super(ExternalAssetDependedBy, cls).__new__(
            cls,
            downstream_asset_key=downstream_asset_key,
            input_name=input_name,
            output_name=output_name,
        )


@whitelist_for_serdes
class ExternalAssetNode(
    namedtuple(
        "_ExternalAssetNode",
        "asset_key dependencies depended_by op_name op_description job_names partitions_def_data output_name output_description",
    )
):
    """A definition of a node in the logical asset graph.

    A function for computing the asset and an identifier for that asset.
    """

    def __new__(
        cls,
        asset_key: AssetKey,
        dependencies: List[ExternalAssetDependency],
        depended_by: List[ExternalAssetDependedBy],
        op_name: Optional[str] = None,
        op_description: Optional[str] = None,
        job_names: Optional[List[str]] = None,
        partitions_def_data: Optional[ExternalPartitionsDefinitionData] = None,
        output_name: Optional[str] = None,
        output_description: Optional[str] = None,
    ):
        return super(ExternalAssetNode, cls).__new__(
            cls,
            asset_key=asset_key,
            dependencies=dependencies,
            depended_by=depended_by,
            op_name=op_name,
            op_description=op_description,
            job_names=job_names,
            partitions_def_data=partitions_def_data,
            output_name=output_name,
            output_description=output_description,
        )


def external_repository_data_from_def(repository_def):
    check.inst_param(repository_def, "repository_def", RepositoryDefinition)

    pipelines = repository_def.get_all_pipelines()
    return ExternalRepositoryData(
        name=repository_def.name,
        external_pipeline_datas=sorted(
            list(map(external_pipeline_data_from_def, pipelines)),
            key=lambda pd: pd.name,
        ),
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
            pipelines, foreign_assets_by_key=repository_def.foreign_assets_by_key
        ),
    )


def external_asset_graph_from_defs(
    pipelines: Sequence[PipelineDefinition], foreign_assets_by_key: Mapping[AssetKey, ForeignAsset]
) -> Sequence[ExternalAssetNode]:
    node_defs_by_asset_key: Dict[
        AssetKey, List[Tuple[OutputDefinition, NodeDefinition, PipelineDefinition]]
    ] = defaultdict(list)

    deps: Dict[AssetKey, Dict[str, ExternalAssetDependency]] = defaultdict(dict)
    dep_by: Dict[AssetKey, List[ExternalAssetDependedBy]] = defaultdict(list)
    all_upstream_asset_keys: Set[AssetKey] = set()

    for pipeline in pipelines:
        for node_def in pipeline.all_node_defs:
            node_upstream_asset_keys = set(
                filter(None, (id.hardcoded_asset_key for id in node_def.input_defs))
            )
            all_upstream_asset_keys.union(node_upstream_asset_keys)

            for output_def in node_def.output_defs:
                asset_key = output_def.hardcoded_asset_key
                if asset_key is None:
                    continue

                node_defs_by_asset_key[asset_key].append((output_def, node_def, pipeline))

                # if not specified, assume depends on all inputs
                in_deps = output_def.in_deps
                if in_deps is None:
                    in_deps = [id.name for id in node_def.input_defs]
                for input_name in in_deps:
                    upstream_asset_key = node_def.input_def_named(input_name).hardcoded_asset_key
                    if upstream_asset_key:
                        deps[asset_key][input_name] = ExternalAssetDependency(
                            upstream_asset_key=upstream_asset_key, input_name=input_name
                        )
                        dep_by[upstream_asset_key].append(
                            ExternalAssetDependedBy(
                                downstream_asset_key=asset_key, input_name=input_name
                            )
                        )

                # if not specified, assume it does not depend on any other outputs
                out_deps = output_def.out_deps or []
                for output_name in out_deps:
                    internal_upstream_asset_key = node_def.output_def_named(
                        output_name
                    ).hardcoded_asset_key
                    if internal_upstream_asset_key:
                        # FIXME: this will break if an input shares a name with an output
                        deps[asset_key][output_name] = ExternalAssetDependency(
                            upstream_asset_key=internal_upstream_asset_key,
                            output_name=output_name,
                        )
                        dep_by[internal_upstream_asset_key].append(
                            ExternalAssetDependedBy(
                                downstream_asset_key=asset_key,
                                output_name=output_name,
                            )
                        )

    asset_keys_without_definitions = all_upstream_asset_keys.difference(
        node_defs_by_asset_key.keys()
    ).difference(foreign_assets_by_key.keys())

    asset_nodes = [
        ExternalAssetNode(
            asset_key=asset_key,
            dependencies=list(deps[asset_key].values()),
            depended_by=dep_by[asset_key],
            job_names=[],
        )
        for asset_key in asset_keys_without_definitions
    ]

    for foreign_asset in foreign_assets_by_key.values():
        if foreign_asset.key in node_defs_by_asset_key:
            raise DagsterInvariantViolationError(
                f"Asset with key {foreign_asset.key.to_string()} is defined both as a foreign asset"
                " and as a non-foreign asset"
            )

        asset_nodes.append(
            ExternalAssetNode(
                asset_key=foreign_asset.key,
                dependencies=list(deps[foreign_asset.key].values()),
                depended_by=dep_by[foreign_asset.key],
                job_names=[],
                op_description=foreign_asset.description,
            )
        )

    for asset_key, node_tuple_list in node_defs_by_asset_key.items():
        output_def, node_def, _ = node_tuple_list[0]
        job_names = [job_def.name for _, _, job_def in node_tuple_list]

        # temporary workaround to retrieve asset partition definition from job
        partitions_def_data = None

        if output_def:
            partitions_def = output_def._asset_partitions_def  # pylint: disable=protected-access
            if partitions_def:
                if isinstance(partitions_def, TimeWindowPartitionsDefinition):
                    partitions_def_data = external_time_window_partitions_definition_from_def(
                        partitions_def
                    )
                elif isinstance(partitions_def, StaticPartitionsDefinition):
                    partitions_def_data = external_static_partitions_definition_from_def(
                        partitions_def
                    )
                else:
                    raise DagsterInvalidDefinitionError(
                        "Only static partition and time window partitions are currently supported."
                    )

        asset_nodes.append(
            ExternalAssetNode(
                asset_key=asset_key,
                dependencies=list(deps[asset_key].values()),
                depended_by=dep_by[asset_key],
                op_name=node_def.name,
                op_description=node_def.description,
                job_names=job_names,
                partitions_def_data=partitions_def_data,
                output_name=output_def.name,
                output_description=output_def.description,
            )
        )

    return asset_nodes


def external_pipeline_data_from_def(pipeline_def):
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


def external_schedule_data_from_def(schedule_def):
    check.inst_param(schedule_def, "schedule_def", ScheduleDefinition)
    return ExternalScheduleData(
        name=schedule_def.name,
        cron_schedule=schedule_def.cron_schedule,
        pipeline_name=schedule_def.pipeline_name,
        solid_selection=schedule_def.solid_selection,
        mode=schedule_def.mode,
        environment_vars=schedule_def.environment_vars,
        partition_set_name=schedule_def.get_partition_set().name
        if isinstance(schedule_def, PartitionScheduleDefinition)
        else None,
        execution_timezone=schedule_def.execution_timezone,
        description=schedule_def.description,
    )


def external_time_window_partitions_definition_from_def(partitions_def):
    check.inst_param(partitions_def, "partitions_def", TimeWindowPartitionsDefinition)
    return ExternalTimeWindowPartitionsDefinitionData(
        schedule_type=partitions_def.schedule_type,
        start=partitions_def.start.timestamp(),
        timezone=partitions_def.timezone,
        fmt=partitions_def.fmt,
        end_offset=partitions_def.end_offset,
    )


def external_static_partitions_definition_from_def(partitions_def):
    check.inst_param(partitions_def, "partitions_def", StaticPartitionsDefinition)
    return ExternalStaticPartitionsDefinitionData(
        partition_keys=partitions_def.get_partition_keys()
    )


def external_partition_set_data_from_def(partition_set_def):
    check.inst_param(partition_set_def, "partition_set_def", PartitionSetDefinition)
    return ExternalPartitionSetData(
        name=partition_set_def.name,
        pipeline_name=partition_set_def.pipeline_name or partition_set_def.job_name,
        solid_selection=partition_set_def.solid_selection,
        mode=partition_set_def.mode,
    )


def external_sensor_data_from_def(sensor_def):
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
    )


def external_preset_data_from_def(preset_def):
    check.inst_param(preset_def, "preset_def", PresetDefinition)
    return ExternalPresetData(
        name=preset_def.name,
        run_config=preset_def.run_config,
        solid_selection=preset_def.solid_selection,
        mode=preset_def.mode,
        tags=preset_def.tags,
    )
