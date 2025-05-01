from dagster._core.definitions.selector import RepositorySelector
from dagster_shared import check

from dagster_graphql.schema.components import GrapheneCodeLocationComponentsManifest
from dagster_graphql.schema.util import ResolveInfo


def fetch_code_location_components_manifest(
    graphene_info: ResolveInfo, repository_selector: RepositorySelector
) -> GrapheneCodeLocationComponentsManifest:
    repository = graphene_info.context.get_code_location(
        repository_selector.location_name
    ).get_repository(repository_selector.repository_name)
    snap = repository.repository_snap
    return GrapheneCodeLocationComponentsManifest(check.not_none(snap.component_manifest))
