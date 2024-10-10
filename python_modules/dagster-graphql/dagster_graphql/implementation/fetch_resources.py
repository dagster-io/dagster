from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.definitions.selector import RepositorySelector, ResourceSelector
from graphene import ResolveInfo

from dagster_graphql.implementation.utils import UserFacingGraphQLError

if TYPE_CHECKING:
    from dagster._core.remote_representation.code_location import CodeLocation

    from dagster_graphql.schema.resources import (
        GrapheneResourceDetails,
        GrapheneResourceDetailsList,
    )


def get_top_level_resources_or_error(
    graphene_info: "ResolveInfo", repository_selector: RepositorySelector
) -> "GrapheneResourceDetailsList":
    from dagster_graphql.schema.resources import (
        GrapheneResourceDetails,
        GrapheneResourceDetailsList,
    )

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location: CodeLocation = graphene_info.context.get_code_location(
        repository_selector.location_name
    )
    repository = location.get_repository(repository_selector.repository_name)
    remote_resources = repository.get_resources()

    results = [
        GrapheneResourceDetails(
            repository_selector.location_name,
            repository_selector.repository_name,
            remote_resource,
        )
        for remote_resource in remote_resources
        if remote_resource.is_top_level
    ]

    return GrapheneResourceDetailsList(results=results)


def get_resource_or_error(
    graphene_info: "ResolveInfo", resource_selector: ResourceSelector
) -> "GrapheneResourceDetails":
    from dagster_graphql.schema.errors import GrapheneResourceNotFoundError
    from dagster_graphql.schema.resources import GrapheneResourceDetails

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(resource_selector, "resource_selector", ResourceSelector)
    location: CodeLocation = graphene_info.context.get_code_location(
        resource_selector.location_name
    )
    repository = location.get_repository(resource_selector.repository_name)

    if not repository.has_resource(resource_selector.resource_name):
        raise UserFacingGraphQLError(
            GrapheneResourceNotFoundError(resource_name=resource_selector.resource_name)
        )

    remote_resource = repository.get_resource(resource_selector.resource_name)

    return GrapheneResourceDetails(
        resource_selector.location_name, resource_selector.repository_name, remote_resource
    )
