from typing import TYPE_CHECKING

from dagster._core.definitions.selector import (
    RepositorySelector,
)
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.schema.errors import GrapheneDuplicateDynamicPartitionError

from ..utils import UserFacingGraphQLError, assert_permission_for_location

if TYPE_CHECKING:
    from ...schema.inputs import GrapheneRepositorySelector
    from ...schema.partition_sets import GrapheneAddDynamicPartitionSuccess


def _repository_contains_dynamic_partitions_def(
    graphene_info, repository_selector: RepositorySelector, partitions_def_name: str
) -> bool:
    from dagster._core.host_representation.external_data import (
        ExternalDynamicPartitionsDefinitionData,
        ExternalMultiPartitionsDefinitionData,
        ExternalPartitionsDefinitionData,
    )

    def _is_matching_partitions_def(partitions_def_data: ExternalPartitionsDefinitionData):
        if isinstance(partitions_def_data, ExternalDynamicPartitionsDefinitionData):
            return partitions_def_data.name == partitions_def_name
        if isinstance(partitions_def_data, ExternalMultiPartitionsDefinitionData):
            return any(
                [
                    _is_matching_partitions_def(dimension.external_partitions_def_data)
                    for dimension in partitions_def_data.external_partition_dimension_definitions
                ]
            )
        return False

    if graphene_info.context.has_code_location(repository_selector.location_name):
        repo_loc = graphene_info.context.get_code_location(repository_selector.location_name)
        if repo_loc.has_repository(repository_selector.repository_name):
            repository = repo_loc.get_repository(repository_selector.repository_name)
            found_partitions_defs = [
                asset_node.partitions_def_data
                for asset_node in repository.external_repository_data.external_asset_graph_data
                if asset_node.partitions_def_data
            ]
            return any(
                [
                    _is_matching_partitions_def(partitions_def)
                    for partitions_def in found_partitions_defs
                ]
            )
    return False


def add_dynamic_partition(
    graphene_info,
    repository_selector: "GrapheneRepositorySelector",
    partitions_def_name: str,
    partition_key: str,
) -> "GrapheneAddDynamicPartitionSuccess":
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError

    from ...schema.partition_sets import GrapheneAddDynamicPartitionSuccess

    unpacked_repository_selector = RepositorySelector.from_graphql_input(repository_selector)

    assert_permission_for_location(
        graphene_info,
        Permissions.EDIT_DYNAMIC_PARTITIONS,
        unpacked_repository_selector.location_name,
    )

    if not _repository_contains_dynamic_partitions_def(
        graphene_info, unpacked_repository_selector, partitions_def_name
    ):
        raise UserFacingGraphQLError(
            GrapheneUnauthorizedError(
                message=(
                    "The repository does not contain a dynamic partitions definition with the given"
                    " name."
                )
            )
        )

    if graphene_info.context.instance.has_dynamic_partition(partitions_def_name, partition_key):
        raise UserFacingGraphQLError(
            GrapheneDuplicateDynamicPartitionError(partitions_def_name, partition_key)
        )

    graphene_info.context.instance.add_dynamic_partitions(partitions_def_name, [partition_key])
    return GrapheneAddDynamicPartitionSuccess(
        partitionsDefName=partitions_def_name, partitionKey=partition_key
    )
