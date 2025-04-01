from collections.abc import Sequence
from typing import TYPE_CHECKING

from dagster._core.definitions.selector import RepositorySelector
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import (
    UserFacingGraphQLError,
    assert_permission_for_location,
)
from dagster_graphql.schema.errors import GrapheneDuplicateDynamicPartitionError

if TYPE_CHECKING:
    from dagster_graphql.schema.inputs import GrapheneRepositorySelector
    from dagster_graphql.schema.partition_sets import (
        GrapheneAddDynamicPartitionSuccess,
        GrapheneDeleteDynamicPartitionsSuccess,
    )


def _repository_contains_dynamic_partitions_def(
    graphene_info, repository_selector: RepositorySelector, partitions_def_name: str
) -> bool:
    from dagster._core.remote_representation.external_data import (
        DynamicPartitionsSnap,
        MultiPartitionsSnap,
        PartitionsSnap,
    )

    def _is_matching_partitions_def(partitions_snap: PartitionsSnap):
        if isinstance(partitions_snap, DynamicPartitionsSnap):
            return partitions_snap.name == partitions_def_name
        if isinstance(partitions_snap, MultiPartitionsSnap):
            return any(
                [
                    _is_matching_partitions_def(dimension.partitions)
                    for dimension in partitions_snap.partition_dimensions
                ]
            )
        return False

    if graphene_info.context.has_code_location(repository_selector.location_name):
        repo_loc = graphene_info.context.get_code_location(repository_selector.location_name)
        if repo_loc.has_repository(repository_selector.repository_name):
            repository = repo_loc.get_repository(repository_selector.repository_name)
            found_partitions_defs = [
                asset_node_snap.partitions
                for asset_node_snap in repository.repository_snap.asset_nodes
                if asset_node_snap.partitions
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
    from dagster_graphql.schema.partition_sets import GrapheneAddDynamicPartitionSuccess

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


def delete_dynamic_partitions(
    graphene_info,
    repository_selector: "GrapheneRepositorySelector",
    partitions_def_name: str,
    partition_keys: Sequence[str],
) -> "GrapheneDeleteDynamicPartitionsSuccess":
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError
    from dagster_graphql.schema.partition_sets import GrapheneDeleteDynamicPartitionsSuccess

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

    for partition_key in partition_keys:
        graphene_info.context.instance.delete_dynamic_partition(partitions_def_name, partition_key)

    return GrapheneDeleteDynamicPartitionsSuccess(partitionsDefName=partitions_def_name)
