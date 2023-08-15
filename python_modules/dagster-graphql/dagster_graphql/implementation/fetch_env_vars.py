from typing import TYPE_CHECKING

import dagster._check as check
from dagster._core.definitions.selector import RepositorySelector
from graphene import ResolveInfo

from dagster_graphql.schema.env_vars import (
    GrapheneEnvVarWithConsumers,
    GrapheneEnvVarWithConsumersList,
    GrapheneEnvVarWithConsumersListOrError,
)

if TYPE_CHECKING:
    from dagster._core.host_representation.code_location import CodeLocation


def get_utilized_env_vars_or_error(
    graphene_info, repository_selector
) -> GrapheneEnvVarWithConsumersListOrError:
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(repository_selector, "repository_selector", RepositorySelector)

    location: CodeLocation = graphene_info.context.get_code_location(
        repository_selector.location_name
    )
    repository = location.get_repository(repository_selector.repository_name)
    utilized_env_vars = repository.get_utilized_env_vars()

    results = [
        GrapheneEnvVarWithConsumers(name=env_var_name, consumers=consumers)
        for env_var_name, consumers in utilized_env_vars.items()
    ]

    return GrapheneEnvVarWithConsumersList(results=results)
