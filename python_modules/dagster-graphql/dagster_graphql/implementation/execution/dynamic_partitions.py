from collections.abc import Sequence
from typing import TYPE_CHECKING

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.selector import RepositorySelector
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import (
    UserFacingGraphQLError,
    assert_permission_for_asset_graph,
    assert_permission_for_location,
)
from dagster_graphql.schema.errors import GrapheneDuplicateDynamicPartitionError

if TYPE_CHECKING:
    from dagster_graphql.schema.inputs import GrapheneRepositorySelector
    from dagster_graphql.schema.partition_sets import (
        GrapheneAddDynamicPartitionSuccess,
        GrapheneDeleteDynamicPartitionsSuccess,
    )


def _get_asset_keys_using_dynamic_partitions_def(
    graphene_info, repository_selector: RepositorySelector, partitions_def_name: str
) -> tuple[Sequence[AssetKey], Sequence[AssetKey]]:
    """Returns the asset keys in the repository that are partitioned by the given dynamic
    partitions definition, split into (assets partitioned directly by the definition,
    multi-partitioned assets with the definition as one of their dimensions).
    """
    from dagster._core.definitions.partitions.snap import (
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

    direct_asset_keys: list[AssetKey] = []
    multi_asset_keys: list[AssetKey] = []
    if graphene_info.context.has_code_location(repository_selector.location_name):
        repo_loc = graphene_info.context.get_code_location(repository_selector.location_name)
        if repo_loc.has_repository(repository_selector.repository_name):
            repository = repo_loc.get_repository(repository_selector.repository_name)
            for asset_node_snap in repository.repository_snap.asset_nodes:
                partitions_snap = asset_node_snap.partitions
                if not partitions_snap or not _is_matching_partitions_def(partitions_snap):
                    continue
                if isinstance(partitions_snap, MultiPartitionsSnap):
                    multi_asset_keys.append(asset_node_snap.asset_key)
                else:
                    direct_asset_keys.append(asset_node_snap.asset_key)
    return direct_asset_keys, multi_asset_keys


def _repository_contains_dynamic_partitions_def(
    graphene_info, repository_selector: RepositorySelector, partitions_def_name: str
) -> bool:
    direct_asset_keys, multi_asset_keys = _get_asset_keys_using_dynamic_partitions_def(
        graphene_info, repository_selector, partitions_def_name
    )
    return bool(direct_asset_keys or multi_asset_keys)


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


def wipe_materializations_for_deleted_partitions(
    graphene_info,
    *,
    partitions_def_name: str,
    partition_keys: Sequence[str],
    direct_asset_keys: Sequence[AssetKey],
    multi_asset_keys: Sequence[AssetKey],
) -> None:
    """Wipes materialization events for the given partition keys from every asset partitioned
    directly by the dynamic partitions definition. Checks permissions and wipe support before
    mutating anything, so a failure leaves both the partition keys and the event log untouched.
    """
    from dagster_graphql.schema.errors import GrapheneUnsupportedOperationError

    affected_asset_keys = [*direct_asset_keys, *multi_asset_keys]
    assert_permission_for_asset_graph(
        graphene_info,
        graphene_info.context.asset_graph,
        affected_asset_keys,
        Permissions.WIPE_ASSETS,
    )

    if multi_asset_keys:
        raise UserFacingGraphQLError(
            GrapheneUnsupportedOperationError(
                message=(
                    "Cannot wipe materializations when deleting partitions of"
                    f" '{partitions_def_name}': it is used as a dimension of multi-partitioned"
                    f" assets ({', '.join(key.to_user_string() for key in multi_asset_keys)}),"
                    " which is not yet supported. The partitions were not deleted."
                )
            )
        )

    for asset_key in direct_asset_keys:
        try:
            graphene_info.context.instance.wipe_asset_partitions(asset_key, partition_keys)
        except NotImplementedError:
            raise UserFacingGraphQLError(
                GrapheneUnsupportedOperationError(
                    message=(
                        "Partitioned asset wipe is not supported by this event log storage."
                        " The partitions were not deleted."
                    )
                )
            )


def delete_dynamic_partitions(
    graphene_info,
    *,
    repository_selector: "GrapheneRepositorySelector",
    partitions_def_name: str,
    partition_keys: Sequence[str],
    wipe_materializations: bool,
) -> "GrapheneDeleteDynamicPartitionsSuccess":
    from dagster_graphql.schema.errors import GrapheneUnauthorizedError
    from dagster_graphql.schema.partition_sets import GrapheneDeleteDynamicPartitionsSuccess

    unpacked_repository_selector = RepositorySelector.from_graphql_input(repository_selector)

    assert_permission_for_location(
        graphene_info,
        Permissions.EDIT_DYNAMIC_PARTITIONS,
        unpacked_repository_selector.location_name,
    )

    direct_asset_keys, multi_asset_keys = _get_asset_keys_using_dynamic_partitions_def(
        graphene_info, unpacked_repository_selector, partitions_def_name
    )

    if not direct_asset_keys and not multi_asset_keys:
        raise UserFacingGraphQLError(
            GrapheneUnauthorizedError(
                message=(
                    "The repository does not contain a dynamic partitions definition with the given"
                    " name."
                )
            )
        )

    if wipe_materializations:
        wipe_materializations_for_deleted_partitions(
            graphene_info,
            partitions_def_name=partitions_def_name,
            partition_keys=partition_keys,
            direct_asset_keys=direct_asset_keys,
            multi_asset_keys=multi_asset_keys,
        )

    for partition_key in partition_keys:
        graphene_info.context.instance.delete_dynamic_partition(partitions_def_name, partition_key)

    return GrapheneDeleteDynamicPartitionsSuccess(partitionsDefName=partitions_def_name)
