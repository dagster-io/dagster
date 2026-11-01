import math
from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING, NamedTuple

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.partitions.definition import MultiPartitionsDefinition
from dagster._core.definitions.selector import RepositorySelector
from dagster._core.workspace.permissions import Permissions

from dagster_graphql.implementation.utils import (
    UserFacingGraphQLError,
    assert_permission_for_asset_graph,
    assert_permission_for_location,
)
from dagster_graphql.schema.errors import (
    GrapheneDuplicateDynamicPartitionError,
    GrapheneUnsupportedOperationError,
)

if TYPE_CHECKING:
    from dagster._core.definitions.partitions.snap import MultiPartitionsSnap

    from dagster_graphql.schema.inputs import GrapheneRepositorySelector
    from dagster_graphql.schema.partition_sets import (
        GrapheneAddDynamicPartitionSuccess,
        GrapheneDeleteDynamicPartitionsSuccess,
    )

# Ceiling on the asset partitions a single delete may wipe. A multi-partitioned asset multiplies
# every deleted key by the size of its other dimensions, so a modest selection can expand into
# millions of keys -- enough to exhaust the web server's memory and to push the resulting
# ASSET_WIPED event, which embeds the whole key list, past downstream message size limits.
MAX_WIPE_ASSET_PARTITIONS = 100000


class MultipartitionedAssetWipeTarget(NamedTuple):
    """A dimension of a multi-partitioned asset that is partitioned by the dynamic partitions
    definition. An asset appears once per matching dimension; the snap is kept so that
    dimension's keys can be expanded into the asset's own multi-partition keys.
    """

    asset_key: AssetKey
    dimension_name: str
    partitions_snap: "MultiPartitionsSnap"


def _other_dimensions_partition_count(
    partitions_def: "MultiPartitionsDefinition", dimension_name: str
) -> int:
    """How many multi-partition keys one key of the named dimension expands into."""
    return math.prod(
        dimension.partitions_def.get_num_partitions()
        for dimension in partitions_def.partitions_defs
        if dimension.name != dimension_name
    )


def _get_asset_keys_using_dynamic_partitions_def(
    graphene_info, repository_selector: RepositorySelector, partitions_def_name: str
) -> tuple[Sequence[AssetKey], Sequence[MultipartitionedAssetWipeTarget]]:
    """Returns the assets in the repository that are partitioned by the given dynamic
    partitions definition, split into (keys of assets partitioned directly by the definition,
    wipe targets for multi-partitioned assets with the definition as one of their dimensions).
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
    multi_targets: list[MultipartitionedAssetWipeTarget] = []
    if graphene_info.context.has_code_location(repository_selector.location_name):
        repo_loc = graphene_info.context.get_code_location(repository_selector.location_name)
        if repo_loc.has_repository(repository_selector.repository_name):
            repository = repo_loc.get_repository(repository_selector.repository_name)
            for asset_node_snap in repository.repository_snap.asset_nodes:
                partitions_snap = asset_node_snap.partitions
                if not partitions_snap or not _is_matching_partitions_def(partitions_snap):
                    continue
                if isinstance(partitions_snap, MultiPartitionsSnap):
                    multi_targets.extend(
                        MultipartitionedAssetWipeTarget(
                            asset_key=asset_node_snap.asset_key,
                            dimension_name=dimension.name,
                            partitions_snap=partitions_snap,
                        )
                        for dimension in partitions_snap.partition_dimensions
                        if _is_matching_partitions_def(dimension.partitions)
                    )
                else:
                    direct_asset_keys.append(asset_node_snap.asset_key)
    return direct_asset_keys, multi_targets


def _repository_contains_dynamic_partitions_def(
    graphene_info, repository_selector: RepositorySelector, partitions_def_name: str
) -> bool:
    direct_asset_keys, multi_targets = _get_asset_keys_using_dynamic_partitions_def(
        graphene_info, repository_selector, partitions_def_name
    )
    return bool(direct_asset_keys or multi_targets)


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
    multi_targets: Sequence[MultipartitionedAssetWipeTarget],
) -> None:
    """Wipes materialization events for the given partition keys from every asset partitioned
    by the dynamic partitions definition, directly or as a multipartition dimension.

    Permissions, wipe support, and key expansion are all resolved before the first wipe, so
    failing any of them leaves the event log untouched.
    """
    from dagster._core.definitions.partitions.context import partition_loading_context

    from dagster_graphql.schema.errors import GrapheneUnsupportedOperationError

    instance = graphene_info.context.instance
    # an asset appears once per matching dimension, so it can be named by more than one target
    multi_asset_keys = list(dict.fromkeys(target.asset_key for target in multi_targets))
    affected_asset_keys = [*direct_asset_keys, *multi_asset_keys]
    assert_permission_for_asset_graph(
        graphene_info,
        graphene_info.context.asset_graph,
        affected_asset_keys,
        Permissions.WIPE_ASSETS,
    )

    if multi_asset_keys and not instance.supports_wipe_on_delete_for_multipartitioned_assets:
        raise UserFacingGraphQLError(
            GrapheneUnsupportedOperationError(
                message=(
                    "Cannot wipe materializations when deleting partitions of"
                    f" '{partitions_def_name}': it is used as a dimension of multi-partitioned"
                    f" assets ({', '.join(key.to_user_string() for key in multi_asset_keys)}),"
                    " which is not enabled for this instance. The partitions were not deleted."
                )
            )
        )

    # Resolve every asset's keys before wiping anything, so a failure to expand one asset's
    # dimension keys leaves the event log untouched.
    keys_to_wipe: list[tuple[AssetKey, Sequence[str]]] = [
        (asset_key, partition_keys) for asset_key in direct_asset_keys
    ]
    if multi_targets:
        # expanding a dimension key needs the other dimensions' keys, which may be dynamic
        with partition_loading_context(dynamic_partitions_store=instance):
            partitions_defs = [
                target.partitions_snap.get_partitions_definition() for target in multi_targets
            ]
            _check_projected_expansions(
                partitions_defs=partitions_defs,
                multi_targets=multi_targets,
                partition_keys=partition_keys,
                direct_asset_keys=direct_asset_keys,
                partitions_def_name=partitions_def_name,
            )

            keys_by_asset: dict[AssetKey, list[str]] = defaultdict(list)
            for target, partitions_def in zip(multi_targets, partitions_defs):
                keys_by_asset[target.asset_key].extend(
                    partitions_def.get_multipartition_keys_with_dimension_values(
                        dimension_name=target.dimension_name,
                        dimension_partition_keys=partition_keys,
                    )
                )
            keys_to_wipe.extend(
                (asset_key, list(dict.fromkeys(keys)))
                for asset_key, keys in keys_by_asset.items()
                if keys
            )

    try:
        for asset_key, keys in keys_to_wipe:
            instance.wipe_asset_partitions(asset_key, keys)
    except NotImplementedError:
        raise UserFacingGraphQLError(
            GrapheneUnsupportedOperationError(
                message=(
                    "Partitioned asset wipe is not supported by this event log storage."
                    " The partitions were not deleted."
                )
            )
        )


def _check_projected_expansions(
    *,
    partitions_defs: list[MultiPartitionsDefinition],
    multi_targets: Sequence[MultipartitionedAssetWipeTarget],
    partition_keys: Sequence[str],
    direct_asset_keys: Sequence[AssetKey],
    partitions_def_name: str,
) -> None:
    expansions = [
        _other_dimensions_partition_count(partitions_def, target.dimension_name)
        for partitions_def, target in zip(partitions_defs, multi_targets)
    ]

    # Check the projected total before building it
    total_asset_partitions = len(partition_keys) * (len(direct_asset_keys) + sum(expansions))
    if total_asset_partitions > MAX_WIPE_ASSET_PARTITIONS:
        message = (
            f"Deleting {len(partition_keys)}"
            f" {'partition' if len(partition_keys) == 1 else 'partitions'} of"
            f" '{partitions_def_name}' would wipe {total_asset_partitions} asset"
            f" partitions, over the limit of {MAX_WIPE_ASSET_PARTITIONS}."
        )
        if len(partition_keys) > 1:
            message += " Try deleting fewer partitions at a time, or wipe the asset materializations separately."
        else:
            message += " Asset materializations must be wiped separately."
        message += " The partitions were not deleted and asset materializations were not wiped."
        raise UserFacingGraphQLError(GrapheneUnsupportedOperationError(message=message))


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

    direct_asset_keys, multi_targets = _get_asset_keys_using_dynamic_partitions_def(
        graphene_info, unpacked_repository_selector, partitions_def_name
    )

    if not direct_asset_keys and not multi_targets:
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
            multi_targets=multi_targets,
        )

    for partition_key in partition_keys:
        graphene_info.context.instance.delete_dynamic_partition(partitions_def_name, partition_key)

    return GrapheneDeleteDynamicPartitionsSuccess(partitionsDefName=partitions_def_name)
