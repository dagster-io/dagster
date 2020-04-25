from collections import OrderedDict, defaultdict

from dagster_graphql.schema.pipelines import DauphinPipeline
from dagster_graphql.schema.solids import (
    DauphinSolidInvocationSite,
    DauphinUsedSolid,
    build_dauphin_solid_handles,
)


def get_solid(graphene_info, name):
    return get_used_solid_map(graphene_info)[name]


def get_solids(graphene_info):
    return get_used_solid_map(graphene_info).values()


def get_used_solid_map(graphene_info):
    inv_by_def_name = defaultdict(list)
    definitions = []

    for active_pipeline in graphene_info.context.get_all_external_pipelines():
        pipeline_index = active_pipeline.pipeline_index
        for handle in build_dauphin_solid_handles(
            pipeline_index, pipeline_index.dep_structure_index
        ):
            definition = handle.solid.get_dauphin_solid_definition()
            if definition.name not in inv_by_def_name:
                definitions.append(definition)
            inv_by_def_name[definition.name].append(
                DauphinSolidInvocationSite(
                    pipeline=DauphinPipeline(active_pipeline), solidHandle=handle,
                )
            )
    return OrderedDict(
        (
            definition.name,
            DauphinUsedSolid(
                definition=definition,
                invocations=sorted(
                    inv_by_def_name[definition.name], key=lambda i: i.solidHandle.handleID
                ),
            ),
        )
        for definition in sorted(definitions, key=lambda d: d.name)
    )
