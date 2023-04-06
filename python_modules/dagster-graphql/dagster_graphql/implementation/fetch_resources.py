from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.definitions.selector import RepositorySelector, ResourceSelector
from dagster._core.host_representation.code_location import CodeLocation
from graphene import ResolveInfo

from .utils import UserFacingGraphQLError, capture_error

if TYPE_CHECKING:
    from ..schema.resources import GrapheneResourceDetails, GrapheneResourceDetailsList


@capture_error
def get_top_level_resources_or_error(
    graphene_info: "ResolveInfo", repository_selector: RepositorySelector
) -> "GrapheneResourceDetailsList":
    from ..schema.resources import GrapheneResourceDetails, GrapheneResourceDetailsList

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location: CodeLocation = graphene_info.context.get_code_location(
        repository_selector.location_name
    )
    repository = location.get_repository(repository_selector.repository_name)
    external_resources = repository.get_external_resources()

    results = [
        GrapheneResourceDetails(
            repository_selector.location_name,
            repository_selector.repository_name,
            external_resource,
        )
        for external_resource in external_resources
        if external_resource.is_top_level
    ]

    return GrapheneResourceDetailsList(results=results)


@capture_error
def get_resource_or_error(
    graphene_info: "ResolveInfo", resource_selector: ResourceSelector
) -> "GrapheneResourceDetails":
    from ..schema.errors import GrapheneResourceNotFoundError
    from ..schema.resources import GrapheneResourceDetails

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(resource_selector, "resource_selector", ResourceSelector)
    location: CodeLocation = graphene_info.context.get_code_location(
        resource_selector.location_name
    )
    repository = location.get_repository(resource_selector.repository_name)

    if not repository.has_external_resource(resource_selector.resource_name):
        raise UserFacingGraphQLError(
            GrapheneResourceNotFoundError(resource_name=resource_selector.resource_name)
        )

    external_resource = repository.get_external_resource(resource_selector.resource_name)

    return GrapheneResourceDetails(
        resource_selector.location_name, resource_selector.repository_name, external_resource
    )
