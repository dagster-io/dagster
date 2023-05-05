from typing import Optional, cast

import dagster._check as check
import graphene
from dagster import MultiPartitionsDefinition
from dagster._core.host_representation import ExternalPartitionSet, RepositoryHandle
from dagster._core.host_representation.external_data import (
    ExternalDynamicPartitionsDefinitionData,
    ExternalMultiPartitionsDefinitionData,
    ExternalPartitionsDefinitionData,
    ExternalStaticPartitionsDefinitionData,
    ExternalTimeWindowPartitionsDefinitionData,
)
from dagster._core.storage.dagster_run import RunsFilter
from dagster._core.storage.tags import PARTITION_NAME_TAG, PARTITION_SET_TAG
from dagster._utils.merger import merge_dicts

from dagster_graphql.implementation.fetch_partition_sets import (
    get_partition_by_name,
    get_partition_config,
    get_partition_set_partition_runs,
    get_partition_set_partition_statuses,
    get_partition_tags,
    get_partitions,
)
from dagster_graphql.implementation.fetch_runs import get_runs

from .asset_key import GrapheneAssetKey
from .backfill import GraphenePartitionBackfill
from .errors import (
    GrapheneDuplicateDynamicPartitionError,
    GraphenePartitionSetNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
    GrapheneUnauthorizedError,
)
from .inputs import GrapheneRunsFilter
from .pipelines.pipeline import GrapheneRun
from .pipelines.status import GrapheneRunStatus
from .repository_origin import GrapheneRepositoryOrigin
from .tags import GraphenePipelineTag
from .util import ResolveInfo, non_null_list


class GrapheneAddDynamicPartitionSuccess(graphene.ObjectType):
    partitionsDefName = graphene.NonNull(graphene.String)
    partitionKey = graphene.NonNull(graphene.String)

    class Meta:
        name = "AddDynamicPartitionSuccess"


class GrapheneAddDynamicPartitionResult(graphene.Union):
    class Meta:
        types = (
            GrapheneAddDynamicPartitionSuccess,
            GrapheneUnauthorizedError,
            GraphenePythonError,
            GrapheneDuplicateDynamicPartitionError,
        )
        name = "AddDynamicPartitionResult"


class GraphenePartitionTags(graphene.ObjectType):
    results = non_null_list(GraphenePipelineTag)

    class Meta:
        name = "PartitionTags"


class GraphenePartitionRunConfig(graphene.ObjectType):
    yaml = graphene.NonNull(graphene.String)

    class Meta:
        name = "PartitionRunConfig"


class GraphenePartitionRunConfigOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionRunConfig, GraphenePythonError)
        name = "PartitionRunConfigOrError"


class GraphenePartitionStatus(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    partitionName = graphene.NonNull(graphene.String)
    runId = graphene.Field(graphene.String)
    runStatus = graphene.Field(GrapheneRunStatus)
    runDuration = graphene.Field(graphene.Float)

    class Meta:
        name = "PartitionStatus"


class GraphenePartitionRun(graphene.ObjectType):
    id = graphene.NonNull(graphene.String)
    partitionName = graphene.NonNull(graphene.String)
    run = graphene.Field(GrapheneRun)

    class Meta:
        name = "PartitionRun"


class GraphenePartitionStatusCounts(graphene.ObjectType):
    runStatus = graphene.NonNull(GrapheneRunStatus)
    count = graphene.NonNull(graphene.Int)

    class Meta:
        name = "PartitionStatusCounts"


class GraphenePartitionStatuses(graphene.ObjectType):
    results = non_null_list(GraphenePartitionStatus)

    class Meta:
        name = "PartitionStatuses"


class GraphenePartitionStatusesOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionStatuses, GraphenePythonError)
        name = "PartitionStatusesOrError"


class GrapheneAssetPartitionsStatusCounts(graphene.ObjectType):
    class Meta:
        name = "AssetPartitionsStatusCounts"

    assetKey = graphene.NonNull(GrapheneAssetKey)
    numPartitionsTargeted = graphene.NonNull(graphene.Int)
    numPartitionsInProgress = graphene.NonNull(graphene.Int)
    numPartitionsMaterialized = graphene.NonNull(graphene.Int)
    numPartitionsFailed = graphene.NonNull(graphene.Int)


class GrapheneUnpartitionedAssetStatus(graphene.ObjectType):
    class Meta:
        name = "UnpartitionedAssetStatus"

    assetKey = graphene.NonNull(GrapheneAssetKey)
    inProgress = graphene.NonNull(graphene.Boolean)
    materialized = graphene.NonNull(graphene.Boolean)
    failed = graphene.NonNull(graphene.Boolean)


class GrapheneAssetBackfillStatus(graphene.Union):
    class Meta:
        types = (GrapheneAssetPartitionsStatusCounts, GrapheneUnpartitionedAssetStatus)
        name = "AssetBackfillStatus"


class GraphenePartitionKeyRange(graphene.ObjectType):
    class Meta:
        name = "PartitionKeyRange"

    start = graphene.NonNull(graphene.String)
    end = graphene.NonNull(graphene.String)


class GraphenePartitionTagsOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionTags, GraphenePythonError)
        name = "PartitionTagsOrError"


class GraphenePartition(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    partition_set_name = graphene.NonNull(graphene.String)
    solid_selection = graphene.List(graphene.NonNull(graphene.String))
    mode = graphene.NonNull(graphene.String)
    runConfigOrError = graphene.NonNull(GraphenePartitionRunConfigOrError)
    tagsOrError = graphene.NonNull(GraphenePartitionTagsOrError)
    runs = graphene.Field(
        non_null_list(GrapheneRun),
        filter=graphene.Argument(GrapheneRunsFilter),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )
    status = graphene.Field(GrapheneRunStatus)

    class Meta:
        name = "Partition"

    def __init__(
        self,
        external_repository_handle: RepositoryHandle,
        external_partition_set: ExternalPartitionSet,
        partition_name: str,
    ):
        self._external_repository_handle = check.inst_param(
            external_repository_handle, "external_respository_handle", RepositoryHandle
        )
        self._external_partition_set = check.inst_param(
            external_partition_set, "external_partition_set", ExternalPartitionSet
        )
        self._partition_name = check.str_param(partition_name, "partition_name")

        super().__init__(
            name=partition_name,
            partition_set_name=external_partition_set.name,
            solid_selection=external_partition_set.solid_selection,
            mode=external_partition_set.mode,
        )

    def resolve_runConfigOrError(self, graphene_info: ResolveInfo):
        return get_partition_config(
            graphene_info,
            self._external_repository_handle,
            self._external_partition_set.name,
            self._partition_name,
        )

    def resolve_tagsOrError(self, graphene_info: ResolveInfo):
        return get_partition_tags(
            graphene_info,
            self._external_repository_handle,
            self._external_partition_set.name,
            self._partition_name,
        )

    def resolve_runs(
        self,
        graphene_info: ResolveInfo,
        filter: Optional[GrapheneRunsFilter] = None,  # noqa: A002
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        partition_tags = {
            PARTITION_SET_TAG: self._external_partition_set.name,
            PARTITION_NAME_TAG: self._partition_name,
        }
        if filter is not None:
            selector = filter.to_selector()
            runs_filter = RunsFilter(
                run_ids=selector.run_ids,
                job_name=selector.job_name,
                statuses=selector.statuses,
                tags=merge_dicts(selector.tags, partition_tags),
            )
        else:
            runs_filter = RunsFilter(tags=partition_tags)

        return get_runs(graphene_info, runs_filter, cursor=cursor, limit=limit)


class GraphenePartitions(graphene.ObjectType):
    results = non_null_list(GraphenePartition)

    class Meta:
        name = "Partitions"


class GraphenePartitionsOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitions, GraphenePythonError)
        name = "PartitionsOrError"


class GraphenePartitionSet(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    name = graphene.NonNull(graphene.String)
    pipeline_name = graphene.NonNull(graphene.String)
    solid_selection = graphene.List(graphene.NonNull(graphene.String))
    mode = graphene.NonNull(graphene.String)
    partitionsOrError = graphene.Field(
        graphene.NonNull(GraphenePartitionsOrError),
        cursor=graphene.String(),
        limit=graphene.Int(),
        reverse=graphene.Boolean(),
    )
    partition = graphene.Field(GraphenePartition, partition_name=graphene.NonNull(graphene.String))
    partitionStatusesOrError = graphene.NonNull(GraphenePartitionStatusesOrError)
    partitionRuns = non_null_list(GraphenePartitionRun)
    repositoryOrigin = graphene.NonNull(GrapheneRepositoryOrigin)
    backfills = graphene.Field(
        non_null_list(GraphenePartitionBackfill),
        cursor=graphene.String(),
        limit=graphene.Int(),
    )

    class Meta:
        name = "PartitionSet"

    def __init__(
        self,
        external_repository_handle: RepositoryHandle,
        external_partition_set: ExternalPartitionSet,
    ):
        self._external_repository_handle = check.inst_param(
            external_repository_handle, "external_respository_handle", RepositoryHandle
        )
        self._external_partition_set = check.inst_param(
            external_partition_set, "external_partition_set", ExternalPartitionSet
        )

        super().__init__(
            name=external_partition_set.name,
            pipeline_name=external_partition_set.job_name,
            solid_selection=external_partition_set.solid_selection,
            mode=external_partition_set.mode,
        )

    def resolve_id(self, _graphene_info: ResolveInfo):
        return self._external_partition_set.get_external_origin_id()

    def resolve_partitionsOrError(
        self,
        graphene_info: ResolveInfo,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        reverse: Optional[bool] = None,
    ):
        return get_partitions(
            graphene_info,
            self._external_repository_handle,
            self._external_partition_set,
            cursor=cursor,
            limit=limit,
            reverse=reverse or False,
        )

    def resolve_partition(self, graphene_info: ResolveInfo, partition_name: str):
        return get_partition_by_name(
            graphene_info,
            self._external_repository_handle,
            self._external_partition_set,
            partition_name,
        )

    def resolve_partitionRuns(self, graphene_info: ResolveInfo):
        return get_partition_set_partition_runs(graphene_info, self._external_partition_set)

    def resolve_partitionStatusesOrError(self, graphene_info: ResolveInfo):
        return get_partition_set_partition_statuses(
            graphene_info,
            self._external_partition_set,
        )

    def resolve_repositoryOrigin(self, _):
        origin = self._external_partition_set.get_external_origin().external_repository_origin
        return GrapheneRepositoryOrigin(origin)

    def resolve_backfills(
        self, graphene_info: ResolveInfo, cursor: Optional[str] = None, limit: Optional[int] = None
    ):
        matching = [
            backfill
            for backfill in graphene_info.context.instance.get_backfills(
                cursor=cursor,
            )
            if backfill.partition_set_origin
            and backfill.partition_set_origin.partition_set_name
            == self._external_partition_set.name
            and backfill.partition_set_origin.external_repository_origin.repository_name
            == self._external_repository_handle.repository_name
        ]
        return [GraphenePartitionBackfill(backfill) for backfill in matching[:limit]]


class GraphenePartitionSetOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionSet, GraphenePartitionSetNotFoundError, GraphenePythonError)
        name = "PartitionSetOrError"


class GraphenePartitionSets(graphene.ObjectType):
    results = non_null_list(GraphenePartitionSet)

    class Meta:
        name = "PartitionSets"


class GraphenePartitionSetsOrError(graphene.Union):
    class Meta:
        types = (GraphenePartitionSets, GraphenePipelineNotFoundError, GraphenePythonError)
        name = "PartitionSetsOrError"


class GraphenePartitionDefinitionType(graphene.Enum):
    TIME_WINDOW = "TIME_WINDOW"
    STATIC = "STATIC"
    MULTIPARTITIONED = "MULTIPARTITIONED"
    DYNAMIC = "DYNAMIC"

    class Meta:
        name = "PartitionDefinitionType"

    @classmethod
    def from_partition_def_data(cls, partition_def_data):
        check.inst_param(partition_def_data, "partition_def_data", ExternalPartitionsDefinitionData)
        if isinstance(partition_def_data, ExternalStaticPartitionsDefinitionData):
            return GraphenePartitionDefinitionType.STATIC
        elif isinstance(partition_def_data, ExternalTimeWindowPartitionsDefinitionData):
            return GraphenePartitionDefinitionType.TIME_WINDOW
        elif isinstance(partition_def_data, ExternalMultiPartitionsDefinitionData):
            return GraphenePartitionDefinitionType.MULTIPARTITIONED
        elif isinstance(partition_def_data, ExternalDynamicPartitionsDefinitionData):
            return GraphenePartitionDefinitionType.DYNAMIC
        else:
            check.failed(
                f"Invalid external partitions definition data type: {type(partition_def_data)}"
            )


class GrapheneDimensionDefinitionType(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    description = graphene.NonNull(graphene.String)
    type = graphene.NonNull(GraphenePartitionDefinitionType)
    isPrimaryDimension = graphene.NonNull(graphene.Boolean)
    dynamicPartitionsDefinitionName = graphene.Field(graphene.String)

    class Meta:
        name = "DimensionDefinitionType"


class GraphenePartitionDefinition(graphene.ObjectType):
    description = graphene.NonNull(graphene.String)
    type = graphene.NonNull(GraphenePartitionDefinitionType)
    dimensionTypes = non_null_list(GrapheneDimensionDefinitionType)
    name = graphene.Field(graphene.String)

    class Meta:
        name = "PartitionDefinition"

    def resolve_dimensionTypes(self, _graphene_info):
        partition_def_data = self._partition_def_data
        return (
            [
                GrapheneDimensionDefinitionType(
                    name=dim.name,
                    description=str(dim.external_partitions_def_data.get_partitions_definition()),
                    type=GraphenePartitionDefinitionType.from_partition_def_data(
                        dim.external_partitions_def_data
                    ),
                    isPrimaryDimension=dim.name
                    == cast(
                        MultiPartitionsDefinition, partition_def_data.get_partitions_definition()
                    ).primary_dimension.name,
                    dynamicPartitionsDefinitionName=dim.external_partitions_def_data.name
                    if isinstance(
                        dim.external_partitions_def_data, ExternalDynamicPartitionsDefinitionData
                    )
                    else None,
                )
                for dim in partition_def_data.external_partition_dimension_definitions
            ]
            if isinstance(partition_def_data, ExternalMultiPartitionsDefinitionData)
            else [
                GrapheneDimensionDefinitionType(
                    name="default",
                    description="",
                    type=GraphenePartitionDefinitionType.from_partition_def_data(
                        partition_def_data
                    ),
                    isPrimaryDimension=True,
                    dynamicPartitionsDefinitionName=partition_def_data.name
                    if isinstance(partition_def_data, ExternalDynamicPartitionsDefinitionData)
                    else None,
                )
            ]
        )

    def __init__(self, partition_def_data: ExternalPartitionsDefinitionData):
        self._partition_def_data = partition_def_data
        super().__init__(
            description=str(partition_def_data.get_partitions_definition()),
            type=GraphenePartitionDefinitionType.from_partition_def_data(partition_def_data),
            name=partition_def_data.name
            if isinstance(partition_def_data, ExternalDynamicPartitionsDefinitionData)
            else None,
        )


class GrapheneDimensionPartitionKeys(graphene.ObjectType):
    name = graphene.NonNull(graphene.String)
    partition_keys = non_null_list(graphene.String)
    type = graphene.NonNull(GraphenePartitionDefinitionType)

    class Meta:
        name = "DimensionPartitionKeys"


types = [
    GraphenePartition,
    GraphenePartitionRunConfig,
    GraphenePartitionRunConfigOrError,
    GraphenePartitions,
    GraphenePartitionSet,
    GraphenePartitionSetOrError,
    GraphenePartitionSets,
    GraphenePartitionSetsOrError,
    GraphenePartitionsOrError,
    GraphenePartitionStatus,
    GraphenePartitionStatusCounts,
    GraphenePartitionStatuses,
    GraphenePartitionStatusesOrError,
    GraphenePartitionTags,
    GraphenePartitionTagsOrError,
]
