import graphene
from dagster import AssetKey, check
from dagster.core.host_representation import ExternalRepository
from dagster.core.host_representation.external_data import ExternalAssetNode

from .asset_key import GrapheneAssetKey
from .errors import GrapheneAssetNotFoundError
from .pipelines.pipeline import GrapheneAssetMaterialization, GraphenePipeline
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
    jobName = graphene.String()
    jobs = non_null_list(GraphenePipeline)
    dependencies = non_null_list(GrapheneAssetDependency)
    dependedBy = non_null_list(GrapheneAssetDependency)
    assetMaterializations = graphene.Field(
        non_null_list(GrapheneAssetMaterialization),
        partitions=graphene.List(graphene.String),
        beforeTimestampMillis=graphene.String(),
        limit=graphene.Int(),
    )

    class Meta:
        name = "AssetNode"

    def __init__(self, external_repository, external_asset_node):
        self._external_repository = check.inst_param(
            external_repository, "external_repository", ExternalRepository
        )
        self._external_asset_node = check.inst_param(
            external_asset_node, "external_asset_node", ExternalAssetNode
        )
        super().__init__(
            id=external_asset_node.asset_key.to_string(),
            assetKey=external_asset_node.asset_key,
            opName=external_asset_node.op_name,
            description=external_asset_node.op_description,
            jobName=external_asset_node.job_names[0] if external_asset_node.job_names else None,
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

    def resolve_assetMaterializations(self, graphene_info, **kwargs):
        from ..implementation.fetch_assets import get_asset_events

        try:
            before_timestamp = (
                int(kwargs.get("beforeTimestampMillis")) / 1000.0
                if kwargs.get("beforeTimestampMillis")
                else None
            )
        except ValueError:
            before_timestamp = None

        return [
            GrapheneAssetMaterialization(event=event)
            for event in get_asset_events(
                graphene_info,
                self._external_asset_node.asset_key,
                kwargs.get("partitions"),
                before_timestamp=before_timestamp,
                limit=kwargs.get("limit"),
            )
        ]

    def resolve_jobs(self, _graphene_info):
        job_names = self._external_asset_node.job_names or []
        return [
            GraphenePipeline(self._external_repository.get_full_external_pipeline(job_name))
            for job_name in job_names
            if self._external_repository.has_external_pipeline(job_name)
        ]


class GrapheneAssetNodeOrError(graphene.Union):
    class Meta:
        types = (GrapheneAssetNode, GrapheneAssetNotFoundError)
        name = "AssetNodeOrError"
