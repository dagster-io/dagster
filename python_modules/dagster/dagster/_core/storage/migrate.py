import asyncio
import logging
from collections.abc import (
    Callable,
    Set as AbstractSet,
)
from typing import TYPE_CHECKING

from dagster_shared.record import record

import dagster._check as check
from dagster._annotations import preview, public
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView
from dagster._core.asset_graph_view.entity_subset import EntitySubset
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.partitions.definition.partitions_definition import (
    PartitionsDefinition,
)
from dagster._core.definitions.partitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.temporal_context import TemporalContext
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._core.execution.context.output import build_output_context
from dagster._core.instance import DagsterInstance
from dagster._core.storage.io_manager import IOManager
from dagster._time import get_current_datetime
from dagster._utils.log import get_dagster_logger

if TYPE_CHECKING:
    from dagster._core.storage.asset_value_loader import AssetValueLoader

logger = logging.getLogger(__name__)


# ########################
# ##### PUBLIC
# ########################


@public
@preview(emit_runtime_warning=False)
@record
class MigrateIOStorageResult:
    """Result of a call to :py:func:`migrate_io_storage`.

    Args:
        migrated: EntitySubsets of assets/partitions that were successfully migrated.
        skipped: EntitySubsets of assets/partitions that were skipped (via ``should_skip``).
        failed: EntitySubsets of assets/partitions that failed to migrate.
    """

    migrated: tuple[EntitySubset[AssetKey], ...]
    skipped: tuple[EntitySubset[AssetKey], ...]
    failed: tuple[EntitySubset[AssetKey], ...]


@public
@preview
def migrate_io_storage(
    *,
    definitions: Definitions | None = None,
    destination_io_manager: IOManager,
    instance: DagsterInstance | None = None,
    context: OpExecutionContext | None = None,
    selection: AssetSelection | None = None,
    should_skip: Callable[[AssetKey, str | None], bool] | None = None,
    batch_partitions: bool = False,
    transform: Callable[[object], object] | None = None,
) -> MigrateIOStorageResult:
    """Migrate asset data from one IO manager to another.

    Reads all materialized assets from a source IO manager and writes them to the
    destination IO manager using ``load_input`` / ``handle_output``. This is useful
    when switching between IO managers (e.g., S3 to GCS, filesystem to S3) without
    re-materializing assets.

    The set of assets to iterate over and the source IO manager for each asset can be
    provided in one of two ways:

    - **Via a ``Definitions`` object** (the ``definitions`` parameter): The assets and
      their IO manager configuration are resolved from the ``Definitions`` object.
      An ``instance`` must also be provided to discover materialized partitions.
    - **Via an ``OpExecutionContext``** (the ``context`` parameter): The assets and
      their IO manager configuration are resolved from the code location that the
      currently executing op belongs to. The ``DagsterInstance`` is obtained from
      the context automatically.

    Exactly one of ``definitions`` or ``context`` must be provided.

    Args:
        definitions (Optional[Definitions]): A Definitions object containing asset
            definitions and their currently-configured IO manager resources (the source).
            Each asset's ``io_manager_key`` is used to resolve the IO manager for loading.
            Mutually exclusive with ``context``.
        destination_io_manager (IOManager): The IO manager to write asset data to.
        instance (Optional[DagsterInstance]): A DagsterInstance used to discover materialized
            assets and partitions. Required when using ``definitions``, ignored when using
            ``context`` (the instance is obtained from the context).
        context (Optional[OpExecutionContext]): An execution context from within an op or
            asset. When provided, the assets and IO managers are resolved from the code
            location, and the instance is obtained from the context. Mutually exclusive
            with ``definitions``.
        selection (Optional[AssetSelection]): An optional asset selection to filter which
            assets to migrate. Defaults to all assets.
        should_skip (Optional[Callable[[AssetKey, Optional[str]], bool]]): An optional
            callback that receives an asset key and partition key (None for unpartitioned
            assets) and returns True if the asset should be skipped.
        batch_partitions (bool): If True, migrates partitioned assets in batches using
            ``PartitionKeyRange`` contexts instead of one partition at a time. The batch
            size is determined by the asset's ``BackfillPolicy.max_partitions_per_run``
            (or all partitions at once if no BackfillPolicy is set). Both the source and
            destination IO managers must support multi-partition contexts. Defaults to False.
        transform (Optional[Callable[[object], object]]): An optional function to transform
            each loaded value before storing it in the destination IO manager. Useful when
            the in-memory Python type differs between source and destination IO managers.

    Returns:
        MigrateIOStorageResult: EntitySubsets of migrated, skipped, and failed assets.
    """
    check.param_invariant(
        (definitions is not None) ^ (context is not None),
        "definitions",
        "Exactly one of 'definitions' or 'context' must be provided.",
    )
    if context is not None:
        repo_def = context.repository_def
        resolved_instance = context.instance
        asset_graph = repo_def.asset_graph
    else:
        assert definitions is not None
        resolved_instance = check.not_none_param(instance, "instance")
        asset_graph = definitions.resolve_asset_graph()

    resolved_destination = destination_io_manager
    dag_logger = get_dagster_logger("migrate_io_storage")
    asset_graph_view = AssetGraphView(
        temporal_context=TemporalContext(
            effective_dt=get_current_datetime(),
            last_event_id=resolved_instance.event_log_storage.get_maximum_record_id(),
        ),
        instance=resolved_instance,
        asset_graph=asset_graph,
    )

    # Resolve selected keys
    if selection is not None:
        selected_keys = selection.resolve(asset_graph)
    else:
        selected_keys = asset_graph.get_all_asset_keys()

    if not selected_keys:
        return MigrateIOStorageResult(migrated=(), skipped=(), failed=())

    # Compute materialized subsets for all selected keys
    materialized_map = asyncio.run(_compute_materialized_subsets(asset_graph_view, selected_keys))
    total_assets = len(materialized_map)
    dag_logger.info(
        "Found %d materialized asset(s) to migrate out of %d selected",
        total_assets,
        len(selected_keys),
    )

    migrated_subsets: list[EntitySubset[AssetKey]] = []
    skipped_subsets: list[EntitySubset[AssetKey]] = []
    failed_subsets: list[EntitySubset[AssetKey]] = []

    if context is not None:
        loader_source = context.repository_def
    else:
        assert definitions is not None
        loader_source = definitions.get_repository_def()

    with loader_source.get_asset_value_loader(instance=resolved_instance) as loader:
        for i, (asset_key, materialized_subset) in enumerate(materialized_map.items(), 1):
            assets_def = asset_graph.assets_def_for_key(asset_key)
            asset_label = asset_key.to_user_string()

            if not materialized_subset.is_partitioned:
                # Unpartitioned asset
                if should_skip is not None and should_skip(asset_key, None):
                    dag_logger.info("[%d/%d] Skipping %s", i, total_assets, asset_label)
                    skipped_subsets.append(materialized_subset)
                    continue
                dag_logger.info("[%d/%d] Migrating %s", i, total_assets, asset_label)
                migrated, _failed = _migrate_single(
                    loader, resolved_destination, asset_key, transform=transform
                )
                if migrated:
                    migrated_subsets.append(materialized_subset)
                else:
                    failed_subsets.append(materialized_subset)
            else:
                # Partitioned asset
                partitions_def = check.not_none(
                    assets_def.partitions_def,
                    "Expected partitions_def for partitioned asset",
                )

                # Filter with should_skip
                migrate_subset = materialized_subset
                if should_skip is not None:
                    keys_to_skip = {
                        pk
                        for pk in materialized_subset.expensively_compute_partition_keys()
                        if should_skip(asset_key, pk)
                    }
                    if keys_to_skip:
                        skip_subset = asset_graph_view.get_subset_from_partition_keys(
                            asset_key, partitions_def, keys_to_skip
                        )
                        skipped_subsets.append(skip_subset)
                        migrate_subset = materialized_subset.compute_difference(skip_subset)

                if migrate_subset.is_empty:
                    dag_logger.info(
                        "[%d/%d] Skipping %s (all partitions skipped)", i, total_assets, asset_label
                    )
                    continue

                num_partitions = migrate_subset.size
                dag_logger.info(
                    "[%d/%d] Migrating %s (%d partition(s)%s)",
                    i,
                    total_assets,
                    asset_label,
                    num_partitions,
                    ", batched" if batch_partitions else "",
                )

                if batch_partitions:
                    batch_size = _get_batch_size(assets_def)
                    m_subset, f_subset = _migrate_partitions_batched(
                        loader,
                        resolved_destination,
                        asset_key,
                        migrate_subset,
                        partitions_def,
                        batch_size,
                        asset_graph_view,
                        transform=transform,
                    )
                    if not m_subset.is_empty:
                        migrated_subsets.append(m_subset)
                    if not f_subset.is_empty:
                        failed_subsets.append(f_subset)
                else:
                    migrated_keys: set[str] = set()
                    failed_keys: set[str] = set()
                    for pk in migrate_subset.expensively_compute_partition_keys():
                        m, _f = _migrate_single(
                            loader, resolved_destination, asset_key, pk, transform=transform
                        )
                        if m:
                            migrated_keys.add(pk)
                        else:
                            failed_keys.add(pk)
                    if migrated_keys:
                        migrated_subsets.append(
                            asset_graph_view.get_subset_from_partition_keys(
                                asset_key, partitions_def, migrated_keys
                            )
                        )
                    if failed_keys:
                        failed_subsets.append(
                            asset_graph_view.get_subset_from_partition_keys(
                                asset_key, partitions_def, failed_keys
                            )
                        )

    total_migrated = sum(s.size for s in migrated_subsets)
    total_skipped = sum(s.size for s in skipped_subsets)
    total_failed = sum(s.size for s in failed_subsets)
    dag_logger.info(
        "Migration complete: %d migrated, %d skipped, %d failed",
        total_migrated,
        total_skipped,
        total_failed,
    )

    return MigrateIOStorageResult(
        migrated=tuple(migrated_subsets),
        skipped=tuple(skipped_subsets),
        failed=tuple(failed_subsets),
    )


# ########################
# ##### HELPERS
# ########################


async def _compute_materialized_subsets(
    asset_graph_view: AssetGraphView,
    selected_keys: AbstractSet[AssetKey],
) -> dict[AssetKey, EntitySubset[AssetKey]]:
    """Compute materialized subsets for all selected keys, skipping unmaterialized assets."""
    result = {}
    for key in selected_keys:
        if not asset_graph_view.asset_graph.get(key).is_materializable:
            continue
        subset = await asset_graph_view.compute_materialized_asset_subset(key)
        if not subset.is_empty:
            result[key] = subset
    return result


def _migrate_single(
    loader: "AssetValueLoader",
    destination_io_manager: IOManager,
    asset_key: AssetKey,
    partition_key: str | None = None,
    *,
    transform: Callable[[object], object] | None = None,
) -> tuple[int, int]:
    """Migrate a single asset/partition. Returns (migrated_count, failed_count)."""
    label = (
        f"asset {asset_key.to_user_string()} partition {partition_key}"
        if partition_key is not None
        else f"asset {asset_key.to_user_string()}"
    )
    try:
        value = loader.load_asset_value(asset_key, partition_key=partition_key)
    except Exception:
        logger.warning("Failed to load %s", label, exc_info=True)
        return 0, 1
    if transform is not None:
        value = transform(value)
    output_ctx = build_output_context(asset_key=asset_key, partition_key=partition_key)
    try:
        destination_io_manager.handle_output(output_ctx, value)
    except Exception:
        logger.warning("Failed to store %s", label, exc_info=True)
        return 0, 1
    return 1, 0


def _get_batch_size(assets_def: AssetsDefinition) -> int | None:
    """Return the batch size from the asset's BackfillPolicy, or None for all-at-once."""
    backfill_policy = assets_def.backfill_policy
    if backfill_policy is None:
        return None
    return backfill_policy.max_partitions_per_run


def _migrate_partitions_batched(
    loader: "AssetValueLoader",
    destination_io_manager: IOManager,
    asset_key: AssetKey,
    migrate_subset: EntitySubset[AssetKey],
    partitions_def: PartitionsDefinition,
    batch_size: int | None,
    asset_graph_view: AssetGraphView,
    *,
    transform: Callable[[object], object] | None = None,
) -> tuple[EntitySubset[AssetKey], EntitySubset[AssetKey]]:
    """Migrate partitions in batches using PartitionKeyRange contexts.

    Returns (migrated_subset, failed_subset).
    """
    partition_subset = migrate_subset.get_internal_subset_value()
    ranges = partition_subset.get_partition_key_ranges(partitions_def)

    migrated_keys: set[str] = set()
    failed_keys: set[str] = set()

    for key_range in ranges:
        sub_ranges = _subdivide_range(partitions_def, key_range, batch_size)

        for sub_range, _num_keys in sub_ranges:
            label = (
                f"asset {asset_key.to_user_string()} partitions {sub_range.start}..{sub_range.end}"
            )
            keys_in_batch = partitions_def.get_partition_keys_in_range(sub_range)

            try:
                value = loader.load_asset_value(asset_key, partition_key_range=sub_range)
            except Exception:
                logger.warning("Failed to load %s", label, exc_info=True)
                failed_keys.update(keys_in_batch)
                continue

            if transform is not None:
                value = transform(value)

            dest_output_ctx = build_output_context(
                asset_key=asset_key,
                asset_partition_key_range=sub_range,
                asset_partitions_def=partitions_def,
            )
            try:
                destination_io_manager.handle_output(dest_output_ctx, value)
            except Exception:
                logger.warning("Failed to store %s", label, exc_info=True)
                failed_keys.update(keys_in_batch)
                continue
            migrated_keys.update(keys_in_batch)

    migrated_subset = (
        asset_graph_view.get_subset_from_partition_keys(asset_key, partitions_def, migrated_keys)
        if migrated_keys
        else asset_graph_view.get_empty_subset(key=asset_key)
    )
    failed_subset = (
        asset_graph_view.get_subset_from_partition_keys(asset_key, partitions_def, failed_keys)
        if failed_keys
        else asset_graph_view.get_empty_subset(key=asset_key)
    )

    return migrated_subset, failed_subset


def _subdivide_range(
    partitions_def: PartitionsDefinition,
    key_range: PartitionKeyRange,
    batch_size: int | None,
) -> list[tuple[PartitionKeyRange, int]]:
    """Split a PartitionKeyRange into sub-ranges of at most batch_size keys.

    Returns a list of (range, num_keys) tuples.
    """
    keys_in_range = partitions_def.get_partition_keys_in_range(key_range)
    if batch_size is None or len(keys_in_range) <= batch_size:
        return [(key_range, len(keys_in_range))]
    result = []
    for i in range(0, len(keys_in_range), batch_size):
        chunk = keys_in_range[i : i + batch_size]
        result.append((PartitionKeyRange(start=chunk[0], end=chunk[-1]), len(chunk)))
    return result
