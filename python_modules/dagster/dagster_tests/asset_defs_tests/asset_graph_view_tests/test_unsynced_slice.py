from typing import Iterable

from dagster import Definitions, asset
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, AssetSlice, SyncStatus
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey, AssetKeyPartitionKey
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.partition import StaticPartitionsDefinition
from dagster._core.instance import DagsterInstance


class AssetGraphViewTester:
    def __init__(self, defs: Definitions, instance: DagsterInstance) -> None:
        self.defs = defs
        self.instance = instance
        self.asset_graph_view = AssetGraphView.for_test(defs, instance)

    def slice(self, asset_key: AssetKey) -> AssetSlice:
        return self.asset_graph_view.get_asset_slice(asset_key)

    def materialize_partitions(self, assets_def: AssetsDefinition, pks: Iterable[str]) -> None:
        for pk in pks:
            assert materialize([assets_def], partition_key=pk, instance=self.instance).success
        self.next_asset_graph_view()

    def next_asset_graph_view(self) -> None:
        self.asset_graph_view = AssetGraphView.for_test(self.defs, self.instance)


def test_static_partitioning_unsynced() -> None:
    letter_keys = {"a", "b", "c"}
    letter_static_partitions_def = StaticPartitionsDefinition(list(letter_keys))

    @asset(partitions_def=letter_static_partitions_def)
    def up() -> None: ...

    @asset(
        deps=[up],
        partitions_def=letter_static_partitions_def,
    )
    def down() -> None: ...

    defs = Definitions([up, down])
    instance = DagsterInstance.ephemeral()
    ag_tester = AssetGraphViewTester(defs, instance)

    def _synced_dict(asset_key: AssetKey, status: SyncStatus, pks: Iterable[str]) -> dict:
        return {AssetKeyPartitionKey(asset_key, pk): status for pk in pks}

    # all missing, all unsynced
    assert ag_tester.slice(up.key).compute_unsynced().compute_partition_keys() == letter_keys
    assert ag_tester.slice(up.key).compute_sync_statuses() == _synced_dict(
        up.key, SyncStatus.UNSYNCED, letter_keys
    )
    assert ag_tester.slice(down.key).compute_unsynced().compute_partition_keys() == letter_keys
    assert ag_tester.slice(down.key).compute_sync_statuses() == _synced_dict(
        down.key, SyncStatus.UNSYNCED, letter_keys
    )

    # materialize all of up
    ag_tester.materialize_partitions(up, letter_keys)

    # all up in sync, all down unsynced
    assert ag_tester.slice(up.key).compute_unsynced().compute_partition_keys() == set()
    assert ag_tester.slice(up.key).compute_sync_statuses() == _synced_dict(
        up.key, SyncStatus.SYNCED, letter_keys
    )
    assert ag_tester.slice(down.key).compute_unsynced().compute_partition_keys() == letter_keys
    assert ag_tester.slice(down.key).compute_unsynced().compute_sync_statuses() == _synced_dict(
        down.key, SyncStatus.UNSYNCED, letter_keys
    )

    # materialize all down. all back in sync
    ag_tester.materialize_partitions(down, letter_keys)
    assert ag_tester.slice(up.key).compute_unsynced().compute_partition_keys() == set()
    assert ag_tester.slice(down.key).compute_unsynced().compute_partition_keys() == set()

    def _of_down(partition_key: str) -> AssetKeyPartitionKey:
        return AssetKeyPartitionKey(down.key, partition_key)

    # materialize only up.b
    ag_tester.materialize_partitions(up, ["b"])
    assert ag_tester.slice(up.key).compute_unsynced().compute_partition_keys() == set()
    assert ag_tester.slice(down.key).compute_unsynced().compute_partition_keys() == {"b"}
    assert ag_tester.slice(down.key).compute_sync_statuses() == {
        _of_down("a"): SyncStatus.SYNCED,
        _of_down("b"): SyncStatus.UNSYNCED,
        _of_down("c"): SyncStatus.SYNCED,
    }

    assert ag_tester.slice(down.key).compute_unsynced().compute_sync_statuses() == {
        _of_down("b"): SyncStatus.UNSYNCED
    }

    # materialize only down.b
    # everything in sync
    ag_tester.materialize_partitions(down, ["b"])
    assert ag_tester.slice(up.key).compute_unsynced().compute_partition_keys() == set()
    assert ag_tester.slice(down.key).compute_unsynced().compute_partition_keys() == set()
