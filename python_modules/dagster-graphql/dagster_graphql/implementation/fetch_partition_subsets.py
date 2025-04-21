from dagster import _check as check

from dagster_graphql.implementation.fetch_assets import get_partition_subsets


def regenerate_and_check_partition_subsets(context, asset_node_snap, dynamic_partitions_loader):
    # TODO - move to implementation dir, type hints
    if not dynamic_partitions_loader:
        check.failed("dynamic_partitions_loader must be provided to get partition keys")

    (
        materialized_partition_subset,
        failed_partition_subset,
        in_progress_subset,
    ) = get_partition_subsets(
        context.instance,
        context,
        asset_node_snap.asset_key,
        dynamic_partitions_loader,
        (
            asset_node_snap.partitions.get_partitions_definition()
            if asset_node_snap.partitions
            else None
        ),
    )

    if (
        materialized_partition_subset is None
        or failed_partition_subset is None
        or in_progress_subset is None
    ):
        check.failed("Expected partitions subset for a partitioned asset")

    return materialized_partition_subset, failed_partition_subset, in_progress_subset
