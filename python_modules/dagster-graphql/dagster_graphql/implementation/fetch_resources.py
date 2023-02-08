import dagster._check as check
from dagster._core.definitions.selector import RepositorySelector, ResourceSelector
from dagster._core.host_representation.repository_location import RepositoryLocation
from graphene import ResolveInfo

from .utils import UserFacingGraphQLError, capture_error


@capture_error
def get_resources_or_error(graphene_info, repository_selector):
    from ..schema.resources import GrapheneResourceDetails, GrapheneResourceDetailsList

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location: RepositoryLocation = graphene_info.context.get_repository_location(
        repository_selector.location_name
    )
    repository = location.get_repository(repository_selector.repository_name)
    external_resources = repository.get_external_resources()

    results = [
        GrapheneResourceDetails(external_resource) for external_resource in external_resources
    ]

    return GrapheneResourceDetailsList(results=results)


@capture_error
def get_resource_or_error(graphene_info, resource_selector: ResourceSelector):
    from ..schema.errors import GrapheneResourceNotFoundError
    from ..schema.resources import GrapheneResourceDetails

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(resource_selector, "resource_selector", ResourceSelector)
    location: RepositoryLocation = graphene_info.context.get_repository_location(
        resource_selector.location_name
    )
    repository = location.get_repository(resource_selector.repository_name)

    if not repository.has_external_resource(resource_selector.resource_name):
        raise UserFacingGraphQLError(
            GrapheneResourceNotFoundError(resource_name=resource_selector.resource_name)
        )

    external_resource = repository.get_external_resource(resource_selector.resource_name)

    return GrapheneResourceDetails(external_resource)
