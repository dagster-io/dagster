from collections import OrderedDict, defaultdict

from dagster import check
from dagster.core.host_representation import ExternalRepository


def get_solid(repo, name):
    return get_used_solid_map(repo)[name]


def get_solids(repo):
    return get_used_solid_map(repo).values()


def get_used_solid_map(repo):
    from ..schema.pipelines.pipeline import GraphenePipeline
    from ..schema.solids import build_solid_handles
    from ..schema.used_solid import (
        GrapheneSolidInvocationSite,
        GrapheneUsedSolid,
    )

    check.inst_param(repo, "repo", ExternalRepository)

    inv_by_def_name = defaultdict(list)
    definitions = []

    for external_pipeline in repo.get_all_external_pipelines():
        for handle in build_solid_handles(external_pipeline, external_pipeline.dep_structure_index):
            definition = handle.solid.get_solid_definition()
            if definition.name not in inv_by_def_name:
                definitions.append(definition)
            inv_by_def_name[definition.name].append(
                GrapheneSolidInvocationSite(
                    pipeline=GraphenePipeline(external_pipeline), solidHandle=handle,
                )
            )

    return OrderedDict(
        (
            definition.name,
            GrapheneUsedSolid(
                definition=definition,
                invocations=sorted(
                    inv_by_def_name[definition.name],
                    key=lambda i: i.solidHandle.handleID.to_string(),
                ),
            ),
        )
        for definition in sorted(definitions, key=lambda d: d.name)
    )
