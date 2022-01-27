import graphene
from dagster import AssetKey, check
from dagster.core.events.log import EventLogEntry
from dagster.core.host_representation import ExternalRepository
from dagster.core.host_representation.external_data import (
    ExternalAssetNode,
    ExternalStaticPartitionsDefinitionData,
    ExternalTimeWindowPartitionsDefinitionData,
)

from . import external
from .asset_key import GrapheneAssetKey
from .errors import GrapheneAssetNotFoundError
from .logs.events import GrapheneMaterializationEvent, GrapheneObservationEvent
from .pipelines.pipeline import GrapheneMaterializationCount, GraphenePipeline
from .util import non_null_list


class GrapheneAssetDependency(graphene.ObjectType):
    class Meta:
        name = "AssetDependency"

    inputName = graphene.NonNull(graphene.String)
    asset = graphene.NonNull("dagster_graphql.schema.asset_graph.GrapheneAssetNode")

    def __init__(self, external_repository, input_name, asset_key):
        self._external_repository = check.inst_param(
            external_repository, "external_repository", ExternalRepository
        )
        self._asset_key = check.inst_param(asset_key, "asset_key", AssetKey)
        super().__init__(inputName=input_name)

    def resolve_asset(self, _graphene_info):
        return GrapheneAssetNode(
            self._external_repository,
            self._external_repository.get_external_asset_node(self._asset_key),
        )


class GrapheneAssetNode(graphene.ObjectType):
    id = graphene.NonNull(graphene.ID)
    assetKey = graphene.NonNull(GrapheneAssetKey)
    description = graphene.String()
    opName = graphene.String()
    jobs = non_null_list(GraphenePipeline)
    repository = graphene.NonNull(lambda: external.GrapheneRepository)
    dependencies = non_null_list(GrapheneAssetDependency)
    dependedBy = non_null_list(GrapheneAssetDependency)
    dependencyKeys = non_null_list(GrapheneAssetKey)
    dependedByKeys = non_null_list(GrapheneAssetKey)
    assetMaterializations = graphene.Field(
        non_null_list(GrapheneMaterializationEvent),
        partitions=graphene.List(graphene.String),
        beforeTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )
    partitionKeys = non_null_list(graphene.String)
    partitionDefinition = graphene.String()
    latestMaterializationByPartition = graphene.Field(
        graphene.NonNull(graphene.List(GrapheneMaterializationEvent)),
        partitions=graphene.List(graphene.String),
    )
    materializationCountByPartition = non_null_list(GrapheneMaterializationCount)
    assetObservations = graphene.Field(
        non_null_list(GrapheneObservationEvent),
        partitions=graphene.List(graphene.String),
        beforeTimestampMillis=graphene.String(),
        afterTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )

    class Meta:
        name = "AssetNode"

    def __init__(
        self,
        external_repository,
        external_asset_node,
        latest_materialization=None,
        fetched_materialization=False,
    ):
        self._external_repository = check.inst_param(
            external_repository, "external_repository", ExternalRepository
        )
        self._external_asset_node = check.inst_param(
            external_asset_node, "external_asset_node", ExternalAssetNode
        )
        self._latest_materialization = check.opt_inst_param(
            latest_materialization, "latest_materialization", EventLogEntry
        )
        # we need a separate flag, because the asset might not have been materialized,
        # so the None value has significance
        self._fetched_materialization = check.bool_param(
            fetched_materialization, "fetched_materialization"
        )

        super().__init__(
            id=external_asset_node.asset_key.to_string(),
            assetKey=external_asset_node.asset_key,
            opName=external_asset_node.op_name,
            description=external_asset_node.op_description,
        )

    def get_external_asset_node(self):
        return self._external_asset_node

    def get_external_repository(self):
        return self._external_repository

    def resolve_repository(self, graphene_info):
        loc = None
        for location in graphene_info.context.repository_locations:
            if self._external_repository in location.get_repositories().values():
                loc = location
        return external.GrapheneRepository(
            graphene_info.context.instance, self._external_repository, loc
        )

    def resolve_dependencies(self, _graphene_info):
        return [
            GrapheneAssetDependency(
                external_repository=self._external_repository,
                input_name=dep.input_name,
                asset_key=dep.upstream_asset_key,
            )
            for dep in self._external_asset_node.dependencies
        ]

    def resolve_dependedBy(self, _graphene_info):
        return [
            GrapheneAssetDependency(
                external_repository=self._external_repository,
                input_name=dep.input_name,
                asset_key=dep.downstream_asset_key,
            )
            for dep in self._external_asset_node.depended_by
        ]

    def resolve_dependencyKeys(self, _graphene_info):
        return [
            GrapheneAssetKey(path=dep.upstream_asset_key.path)
            for dep in self._external_asset_node.dependencies
        ]

    def resolve_dependedByKeys(self, _graphene_info):
        return [
            GrapheneAssetKey(path=dep.downstream_asset_key.path)
            for dep in self._external_asset_node.depended_by
        ]

    def resolve_assetMaterializations(self, graphene_info, **kwargs):
        from ..implementation.fetch_assets import get_asset_materializations

        try:
            before_timestamp = (
                int(kwargs.get("beforeTimestampMillis")) / 1000.0
                if kwargs.get("beforeTimestampMillis")
                else None
            )
        except ValueError:
            before_timestamp = None

        limit = kwargs.get("limit")
        partitions = kwargs.get("partitions")
        if self._fetched_materialization and limit == 1 and not partitions and not before_timestamp:
            return (
                [
                    GrapheneMaterializationEvent(
                        event=self._latest_materialization,
                    )
                ]
                if self._latest_materialization
                else []
            )

        return [
            GrapheneMaterializationEvent(event=event)
            for event in get_asset_materializations(
                graphene_info,
                self._external_asset_node.asset_key,
                partitions,
                before_timestamp=before_timestamp,
                limit=limit,
            )
        ]

    def resolve_jobs(self, _graphene_info):
        job_names = self._external_asset_node.job_names or []
        return [
            GraphenePipeline(self._external_repository.get_full_external_pipeline(job_name))
            for job_name in job_names
            if self._external_repository.has_external_pipeline(job_name)
        ]

    def get_partition_keys(self):
        # TODO: Add functionality for dynamic partitions definition
        partitions_def_data = self._external_asset_node.partitions_def_data
        if partitions_def_data:
            if isinstance(
                partitions_def_data, ExternalStaticPartitionsDefinitionData
            ) or isinstance(partitions_def_data, ExternalTimeWindowPartitionsDefinitionData):
                return [
                    partition.name
                    for partition in partitions_def_data.get_partitions_definition().get_partitions()
                ]
        return []

    def resolve_partitionKeys(self, _graphene_info):
        return self.get_partition_keys()

    def resolve_partitionDefinition(self, _graphene_info):
        partitions_def_data = self._external_asset_node.partitions_def_data
        if partitions_def_data:
            return str(partitions_def_data.get_partitions_definition())
        return None

    def resolve_latestMaterializationByPartition(self, _graphene_info, **kwargs):
        from ..implementation.fetch_assets import get_asset_materializations

        get_partition = (
            lambda event: event.dagster_event.step_materialization_data.materialization.partition
        )

        partitions = kwargs.get("partitions") or self.get_partition_keys()

        events_for_partitions = get_asset_materializations(
            _graphene_info,
            self._external_asset_node.asset_key,
            partitions,
        )

        latest_materialization_by_partition = {}
        for event in events_for_partitions:  # events are sorted in order of newest to oldest
            event_partition = get_partition(event)
            if event_partition not in latest_materialization_by_partition:
                latest_materialization_by_partition[event_partition] = event
            if len(latest_materialization_by_partition) == len(partitions):
                break

        # return materializations in the same order as the provided partitions, None if
        # materialization does not exist
        ordered_materializations = [
            latest_materialization_by_partition.get(partition) for partition in partitions
        ]

        return [
            GrapheneMaterializationEvent(event=event) if event else None
            for event in ordered_materializations
        ]

    def resolve_materializationCountByPartition(self, _graphene_info):
        asset_key = self._external_asset_node.asset_key
        partition_keys = self.get_partition_keys()

        count_by_partition = _graphene_info.context.instance.get_materialization_count_by_partition(
            [self._external_asset_node.asset_key]
        )[asset_key]

        return [
            GrapheneMaterializationCount(partition_key, count_by_partition.get(partition_key, 0))
            for partition_key in partition_keys
        ]

    def resolve_assetObservations(self, graphene_info, **kwargs):
        from ..implementation.fetch_assets import get_asset_observations

        try:
            before_timestamp = (
                int(kwargs.get("beforeTimestampMillis")) / 1000.0
                if kwargs.get("beforeTimestampMillis")
                else None
            )
        except ValueError:
            before_timestamp = None

        try:
            after_timestamp = (
                int(kwargs.get("afterTimestampMillis")) / 1000.0
                if kwargs.get("afterTimestampMillis")
                else None
            )
        except ValueError:
            after_timestamp = None

        return [
            GrapheneObservationEvent(event=event)
            for event in get_asset_observations(
                graphene_info,
                self._external_asset_node.asset_key,
                kwargs.get("partitions"),
                before_timestamp=before_timestamp,
                after_timestamp=after_timestamp,
                limit=kwargs.get("limit"),
            )
        ]


class GrapheneAssetNodeOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetNode, GrapheneAssetNotFoundError)
        name = "AssetNodeOrError"
