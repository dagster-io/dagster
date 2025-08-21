from collections import OrderedDict, defaultdict

import dagster._check as check
from dagster._core.remote_representation.external import RemoteRepository

from dagster_graphql.implementation.utils import GraphSelector


def get_solid(repo, name):
    return get_used_solid_map(repo)[name]


def get_solids(repo):
    return get_used_solid_map(repo).values()


def get_used_solid_map(repo):
    from dagster_graphql.schema.pipelines.pipeline import GraphenePipeline
    from dagster_graphql.schema.solids import build_solid_handles
    from dagster_graphql.schema.used_solid import GrapheneNodeInvocationSite, GrapheneUsedSolid

    check.inst_param(repo, "repo", RemoteRepository)

    inv_by_def_name = defaultdict(list)
    definitions = []

    for external_pipeline in repo.get_all_jobs():
        for handle in build_solid_handles(external_pipeline).values():
            definition = handle.solid.get_solid_definition()
            if definition.name not in inv_by_def_name:
                definitions.append(definition)
            inv_by_def_name[definition.name].append(
                GrapheneNodeInvocationSite(
                    pipeline=GraphenePipeline(external_pipeline),
                    solidHandle=handle,
                )
            )

    return OrderedDict(
        (
            definition.name,
            GrapheneUsedSolid(
                definition=definition,
                invocations=sorted(
                    inv_by_def_name[definition.name],
                    key=lambda i: str(i.solidHandle.handleID),
                ),
            ),
        )
        for definition in sorted(definitions, key=lambda d: d.name)
    )


def get_graph_or_error(graphene_info, graph_selector):
    from dagster_graphql.schema.errors import GrapheneGraphNotFoundError
    from dagster_graphql.schema.pipelines.pipeline import GrapheneGraph
    from dagster_graphql.schema.solids import build_solid_handles

    check.inst_param(graph_selector, "graph_selector", GraphSelector)
    if not graphene_info.context.has_code_location(graph_selector.location_name):
        return GrapheneGraphNotFoundError(selector=graph_selector)

    repo_loc = graphene_info.context.get_code_location(graph_selector.location_name)
    if not repo_loc.has_repository(graph_selector.repository_name):
        return GrapheneGraphNotFoundError(selector=graph_selector)

    repository = repo_loc.get_repository(graph_selector.repository_name)

    for external_pipeline in repository.get_all_jobs():
        # first check for graphs
        if external_pipeline.get_graph_name() == graph_selector.graph_name:
            return GrapheneGraph(external_pipeline)

        for handle in build_solid_handles(external_pipeline).values():
            definition = handle.solid.get_solid_definition()
            if definition.name == graph_selector.graph_name:
                return GrapheneGraph(external_pipeline, str(handle.handleID))

    return GrapheneGraphNotFoundError(selector=graph_selector)
