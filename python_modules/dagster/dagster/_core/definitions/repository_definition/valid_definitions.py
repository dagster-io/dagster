from typing import TYPE_CHECKING, Dict, Sequence, TypeVar, Union

from typing_extensions import TypeAlias

from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.schedule_definition import ScheduleDefinition
from dagster._core.definitions.sensor_definition import SensorDefinition
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition

if TYPE_CHECKING:
    from dagster._core.definitions import AssetsDefinition
    from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
    from dagster._core.definitions.partitioned_schedule import (
        UnresolvedPartitionedAssetScheduleDefinition,
    )

SINGLETON_REPOSITORY_NAME = "__repository__"

VALID_REPOSITORY_DATA_DICT_KEYS = {
    "schedules",
    "sensors",
    "jobs",
}

T_RepositoryLevelDefinition = TypeVar(
    "T_RepositoryLevelDefinition",
    JobDefinition,
    ScheduleDefinition,
    SensorDefinition,
)

RepositoryElementDefinition: TypeAlias = Union[
    "AssetsDefinition",
    GraphDefinition,
    JobDefinition,
    ScheduleDefinition,
    SensorDefinition,
    SourceAsset,
    UnresolvedAssetJobDefinition,
    "UnresolvedPartitionedAssetScheduleDefinition",
]

RepositoryDictSpec: TypeAlias = Dict[str, Dict[str, RepositoryElementDefinition]]

RepositoryListSpec: TypeAlias = Sequence[
    Union[RepositoryElementDefinition, "CacheableAssetsDefinition"]
]
