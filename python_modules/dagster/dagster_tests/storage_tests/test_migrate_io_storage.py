import logging
import tempfile
from unittest.mock import MagicMock

import dagster as dg
from dagster import AssetKey, DagsterInstance, FilesystemIOManager
from dagster._core.execution.context.input import build_input_context
from dagster._core.execution.context.output import build_output_context
from dagster._core.storage.fs_io_manager import PickledObjectFilesystemIOManager
from dagster._core.storage.io_manager import IOManager
from dagster._core.storage.migrate import migrate_io_storage

# ########################
# ##### HELPERS
# ########################


def _load_from(
    io_manager: IOManager,
    asset_key: AssetKey,
    partition_key: str | None = None,
) -> object:
    """Load a value from an IO manager for test verification."""
    output_ctx = build_output_context(asset_key=asset_key, partition_key=partition_key)
    input_ctx = build_input_context(
        asset_key=asset_key, partition_key=partition_key, upstream_output=output_ctx
    )
    return io_manager.load_input(input_ctx)


def _subset_size(subsets):
    """Sum the sizes of a sequence of EntitySubsets."""
    return sum(s.size for s in subsets)


# ########################
# ##### TESTS
# ########################


def test_migrate_unpartitioned_assets(caplog):
    """Materialize 2 unpartitioned assets, migrate, verify values and logging."""

    @dg.asset
    def asset_one() -> dict:
        return {"key": "value1"}

    @dg.asset
    def asset_two() -> dict:
        return {"key": "value2"}

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [asset_one, asset_two],
            instance=instance,
            resources={"io_manager": source_factory},
        )

        definitions = dg.Definitions(
            assets=[asset_one, asset_two],
            resources={"io_manager": source_factory},
        )

        with caplog.at_level(logging.INFO, logger="dagster.builtin.migrate_io_storage"):
            result = migrate_io_storage(
                definitions=definitions, destination_io_manager=destination, instance=instance
            )

        assert _subset_size(result.migrated) == 2
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0
        assert _load_from(destination, AssetKey("asset_one")) == {"key": "value1"}
        assert _load_from(destination, AssetKey("asset_two")) == {"key": "value2"}

        # Verify progress logging
        assert "Found 2 materialized asset(s) to migrate" in caplog.text
        assert "Migrating asset_one" in caplog.text
        assert "Migrating asset_two" in caplog.text
        assert "Migration complete: 2 migrated, 0 skipped, 0 failed" in caplog.text


def test_migrate_partitioned_assets(caplog):
    """Materialize a daily-partitioned asset for 2 partitions, verify logging."""
    daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

    @dg.asset(partitions_def=daily)
    def partitioned_asset(context: dg.AssetExecutionContext) -> dict:
        return {"date": context.partition_key}

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        for pk in ["2024-01-01", "2024-01-02"]:
            dg.materialize(
                [partitioned_asset],
                instance=instance,
                resources={"io_manager": source_factory},
                partition_key=pk,
            )

        definitions = dg.Definitions(
            assets=[partitioned_asset],
            resources={"io_manager": source_factory},
        )

        with caplog.at_level(logging.INFO, logger="dagster.builtin.migrate_io_storage"):
            result = migrate_io_storage(
                definitions=definitions, destination_io_manager=destination, instance=instance
            )

        assert _subset_size(result.migrated) == 2
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0
        assert _load_from(destination, AssetKey("partitioned_asset"), "2024-01-01") == {
            "date": "2024-01-01"
        }
        assert _load_from(destination, AssetKey("partitioned_asset"), "2024-01-02") == {
            "date": "2024-01-02"
        }

        # Verify partitioned progress logging
        assert "Migrating partitioned_asset (2 partition(s))" in caplog.text
        assert "Migration complete: 2 migrated, 0 skipped, 0 failed" in caplog.text


def test_migrate_mixed_assets():
    """Migrate unpartitioned + partitioned assets together."""
    daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

    @dg.asset
    def simple_asset() -> str:
        return "hello"

    @dg.asset(partitions_def=daily)
    def daily_asset(context: dg.AssetExecutionContext) -> str:
        return f"data-{context.partition_key}"

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [simple_asset],
            instance=instance,
            resources={"io_manager": source_factory},
        )
        for pk in ["2024-01-01", "2024-01-02"]:
            dg.materialize(
                [daily_asset],
                instance=instance,
                resources={"io_manager": source_factory},
                partition_key=pk,
            )

        definitions = dg.Definitions(
            assets=[simple_asset, daily_asset],
            resources={"io_manager": source_factory},
        )

        result = migrate_io_storage(
            definitions=definitions, destination_io_manager=destination, instance=instance
        )

        assert _subset_size(result.migrated) == 3
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0
        assert _load_from(destination, AssetKey("simple_asset")) == "hello"
        assert _load_from(destination, AssetKey("daily_asset"), "2024-01-01") == "data-2024-01-01"


def test_unmaterialized_assets_are_skipped():
    """Define but don't materialize an asset — it won't appear."""

    @dg.asset
    def materialized_asset() -> str:
        return "exists"

    @dg.asset
    def unmaterialized_asset() -> str:
        return "never run"

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [materialized_asset],
            instance=instance,
            resources={"io_manager": source_factory},
        )

        definitions = dg.Definitions(
            assets=[materialized_asset, unmaterialized_asset],
            resources={"io_manager": source_factory},
        )

        result = migrate_io_storage(
            definitions=definitions, destination_io_manager=destination, instance=instance
        )

        assert _subset_size(result.migrated) == 1
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0
        assert _load_from(destination, AssetKey("materialized_asset")) == "exists"


def test_should_skip_callback(caplog):
    """Skip one asset via callback, verify it's skipped and logged."""

    @dg.asset
    def asset_a() -> str:
        return "a_value"

    @dg.asset
    def asset_b() -> str:
        return "b_value"

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [asset_a, asset_b],
            instance=instance,
            resources={"io_manager": source_factory},
        )

        def skip_asset_a(asset_key: AssetKey, _partition_key: str | None) -> bool:
            return asset_key == AssetKey("asset_a")

        definitions = dg.Definitions(
            assets=[asset_a, asset_b],
            resources={"io_manager": source_factory},
        )

        with caplog.at_level(logging.INFO, logger="dagster.builtin.migrate_io_storage"):
            result = migrate_io_storage(
                definitions=definitions,
                destination_io_manager=destination,
                instance=instance,
                should_skip=skip_asset_a,
            )

        assert _subset_size(result.migrated) == 1
        assert _subset_size(result.skipped) == 1
        assert _subset_size(result.failed) == 0
        assert _load_from(destination, AssetKey("asset_b")) == "b_value"

        # Verify skip is logged
        assert "Skipping asset_a" in caplog.text
        assert "Migration complete: 1 migrated, 1 skipped, 0 failed" in caplog.text


def test_asset_selection():
    """Use AssetSelection to migrate only a subset of assets."""

    @dg.asset
    def asset_a() -> str:
        return "a_value"

    @dg.asset
    def asset_b() -> str:
        return "b_value"

    @dg.asset
    def asset_c() -> str:
        return "c_value"

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [asset_a, asset_b, asset_c],
            instance=instance,
            resources={"io_manager": source_factory},
        )

        definitions = dg.Definitions(
            assets=[asset_a, asset_b, asset_c],
            resources={"io_manager": source_factory},
        )

        result = migrate_io_storage(
            definitions=definitions,
            destination_io_manager=destination,
            instance=instance,
            selection=dg.AssetSelection.assets(asset_a, asset_c),
        )

        assert _subset_size(result.migrated) == 2
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0
        assert _load_from(destination, AssetKey("asset_a")) == "a_value"
        assert _load_from(destination, AssetKey("asset_c")) == "c_value"


def test_failed_load():
    """Source IO manager raises on one asset, verify failed count."""

    @dg.asset
    def good_asset() -> str:
        return "good"

    @dg.asset
    def bad_asset() -> str:
        return "bad"

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        real_source = PickledObjectFilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [good_asset, bad_asset],
            instance=instance,
            resources={"io_manager": source_factory},
        )

        mock_source = MagicMock(spec=IOManager)

        def load_input_side_effect(context):
            if context.asset_key == AssetKey("bad_asset"):
                raise RuntimeError("Simulated IO failure")
            return real_source.load_input(context)

        mock_source.load_input.side_effect = load_input_side_effect

        definitions = dg.Definitions(
            assets=[good_asset, bad_asset],
            resources={"io_manager": mock_source},
        )

        result = migrate_io_storage(
            definitions=definitions, destination_io_manager=destination, instance=instance
        )

        assert _subset_size(result.migrated) == 1
        assert _subset_size(result.failed) == 1
        assert _subset_size(result.skipped) == 0
        assert _load_from(destination, AssetKey("good_asset")) == "good"


def test_empty_instance():
    """No materialized assets — verify empty result."""

    @dg.asset
    def some_asset() -> str:
        return "value"

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source = PickledObjectFilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        definitions = dg.Definitions(
            assets=[some_asset],
            resources={"io_manager": source},
        )

        result = migrate_io_storage(
            definitions=definitions, destination_io_manager=destination, instance=instance
        )

        assert _subset_size(result.migrated) == 0
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0


def test_batch_partitions():
    """Migrate partitioned asset with batch_partitions=True."""
    daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

    @dg.asset(partitions_def=daily)
    def partitioned_asset(context: dg.AssetExecutionContext) -> dict:
        return {"date": context.partition_key}

    with (
        tempfile.TemporaryDirectory() as src_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)

        for pk in ["2024-01-01", "2024-01-02", "2024-01-03"]:
            dg.materialize(
                [partitioned_asset],
                instance=instance,
                resources={"io_manager": source_factory},
                partition_key=pk,
            )

        mock_dest = MagicMock(spec=IOManager)

        definitions = dg.Definitions(
            assets=[partitioned_asset],
            resources={"io_manager": source_factory},
        )

        result = migrate_io_storage(
            definitions=definitions,
            destination_io_manager=mock_dest,
            instance=instance,
            batch_partitions=True,
        )

        assert _subset_size(result.migrated) == 3
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0
        # 3 contiguous partitions — loaded and written in a single batch
        assert mock_dest.handle_output.call_count == 1


def test_batch_partitions_with_backfill_policy():
    """Batch size is determined by BackfillPolicy.max_partitions_per_run."""
    daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

    @dg.asset(
        partitions_def=daily,
        backfill_policy=dg.BackfillPolicy.multi_run(max_partitions_per_run=2),
    )
    def partitioned_asset(context: dg.AssetExecutionContext) -> dict:
        return {"date": context.partition_key}

    with (
        tempfile.TemporaryDirectory() as src_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)

        for pk in ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]:
            dg.materialize(
                [partitioned_asset],
                instance=instance,
                resources={"io_manager": source_factory},
                partition_key=pk,
            )

        mock_dest = MagicMock(spec=IOManager)

        definitions = dg.Definitions(
            assets=[partitioned_asset],
            resources={"io_manager": source_factory},
        )

        result = migrate_io_storage(
            definitions=definitions,
            destination_io_manager=mock_dest,
            instance=instance,
            batch_partitions=True,
        )

        assert _subset_size(result.migrated) == 5
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0
        # 5 partitions with batch_size=2 => 3 batches (2+2+1)
        assert mock_dest.handle_output.call_count == 3


def test_transform():
    """Transform values during migration."""

    @dg.asset
    def my_asset() -> dict:
        return {"key": "value"}

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [my_asset],
            instance=instance,
            resources={"io_manager": source_factory},
        )

        definitions = dg.Definitions(
            assets=[my_asset],
            resources={"io_manager": source_factory},
        )

        def add_extra_field(value):
            return {**value, "extra": "added"}

        result = migrate_io_storage(
            definitions=definitions,
            destination_io_manager=destination,
            instance=instance,
            transform=add_extra_field,
        )

        assert _subset_size(result.migrated) == 1
        loaded = _load_from(destination, AssetKey("my_asset"))
        assert loaded == {"key": "value", "extra": "added"}


def test_result_entity_subsets():
    """Verify that MigrateIOStorageResult contains proper EntitySubsets."""
    daily = dg.DailyPartitionsDefinition(start_date="2024-01-01")

    @dg.asset
    def unpart_asset() -> str:
        return "hello"

    @dg.asset(partitions_def=daily)
    def part_asset(context: dg.AssetExecutionContext) -> str:
        return f"data-{context.partition_key}"

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [unpart_asset],
            instance=instance,
            resources={"io_manager": source_factory},
        )
        for pk in ["2024-01-01", "2024-01-02", "2024-01-03"]:
            dg.materialize(
                [part_asset],
                instance=instance,
                resources={"io_manager": source_factory},
                partition_key=pk,
            )

        def skip_one_partition(asset_key: AssetKey, partition_key: str | None) -> bool:
            return partition_key == "2024-01-02"

        definitions = dg.Definitions(
            assets=[unpart_asset, part_asset],
            resources={"io_manager": source_factory},
        )

        result = migrate_io_storage(
            definitions=definitions,
            destination_io_manager=destination,
            instance=instance,
            should_skip=skip_one_partition,
        )

        # Verify EntitySubset structure
        assert len(result.migrated) == 2  # unpart_asset + part_asset (2 partitions)
        assert len(result.skipped) == 1  # part_asset (1 partition)

        # Verify the skipped subset contains the right partition
        skipped_subset = result.skipped[0]
        assert skipped_subset.key == AssetKey("part_asset")
        assert skipped_subset.size == 1
        assert "2024-01-02" in skipped_subset.expensively_compute_partition_keys()

        # Verify the migrated partitioned subset
        part_migrated = [s for s in result.migrated if s.key == AssetKey("part_asset")]
        assert len(part_migrated) == 1
        assert part_migrated[0].size == 2
        migrated_pks = part_migrated[0].expensively_compute_partition_keys()
        assert "2024-01-01" in migrated_pks
        assert "2024-01-03" in migrated_pks


def test_migrate_with_context():
    """Migrate assets using OpExecutionContext instead of Definitions."""

    @dg.asset
    def asset_one() -> dict:
        return {"key": "value1"}

    @dg.asset
    def asset_two() -> dict:
        return {"key": "value2"}

    with (
        tempfile.TemporaryDirectory() as src_dir,
        tempfile.TemporaryDirectory() as dst_dir,
        DagsterInstance.ephemeral() as instance,
    ):
        source_factory = FilesystemIOManager(base_dir=src_dir)
        destination = PickledObjectFilesystemIOManager(base_dir=dst_dir)

        dg.materialize(
            [asset_one, asset_two],
            instance=instance,
            resources={"io_manager": source_factory},
        )

        definitions = dg.Definitions(
            assets=[asset_one, asset_two],
            resources={"io_manager": source_factory},
        )
        repo_def = definitions.get_repository_def()

        mock_context = MagicMock(spec=dg.OpExecutionContext)
        mock_context.repository_def = repo_def
        mock_context.instance = instance

        result = migrate_io_storage(
            context=mock_context,
            destination_io_manager=destination,
        )

        assert _subset_size(result.migrated) == 2
        assert _subset_size(result.skipped) == 0
        assert _subset_size(result.failed) == 0
        assert _load_from(destination, AssetKey("asset_one")) == {"key": "value1"}
        assert _load_from(destination, AssetKey("asset_two")) == {"key": "value2"}
