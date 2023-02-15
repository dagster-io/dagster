from typing import TYPE_CHECKING, TypeVar, Union

from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.partition import PartitionSetDefinition
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

if TYPE_CHECKING:
    from dagster._core.definitions import AssetGroup, AssetsDefinition
    from dagster._core.definitions.partitioned_schedule import (
        UnresolvedPartitionedAssetScheduleDefinition,
    )

SINGLETON_REPOSITORY_NAME = "__repository__"

VALID_REPOSITORY_DATA_DICT_KEYS = {
    "pipelines",
    "partition_sets",
    "schedules",
    "sensors",
    "jobs",
}

RepositoryLevelDefinition = TypeVar(
    "RepositoryLevelDefinition",
    PipelineDefinition,
    JobDefinition,
    PartitionSetDefinition,
    ScheduleDefinition,
    SensorDefinition,
)

RepositoryListDefinition = Union[
    "AssetsDefinition",
    "AssetGroup",
    GraphDefinition,
    PartitionSetDefinition[object],
    PipelineDefinition,
    ScheduleDefinition,
    SensorDefinition,
    SourceAsset,
    UnresolvedAssetJobDefinition,
    "UnresolvedPartitionedAssetScheduleDefinition",
]
