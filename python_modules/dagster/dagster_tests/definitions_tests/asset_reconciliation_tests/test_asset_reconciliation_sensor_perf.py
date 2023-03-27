import os
import random
import tarfile
import tempfile
import time
from typing import AbstractSet, NamedTuple, Optional, Sequence, Tuple

import pytest
from dagster import (
    AssetKey,
    AssetSelection,
    DagsterInstance,
    DailyPartitionsDefinition,
    asset,
    repository,
)
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.asset_out import AssetOut
from dagster._core.definitions.asset_reconciliation_sensor import build_asset_reconciliation_sensor
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.decorators.asset_decorator import multi_asset
from dagster._core.definitions.events import Output
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.definitions.materialize import materialize_to_memory
from dagster._core.definitions.partition import PartitionsDefinition
from dagster._core.definitions.partition_key_range import PartitionKeyRange
from dagster._core.definitions.repository_definition import RepositoryDefinition
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.definitions.time_window_partitions import HourlyPartitionsDefinition
from dagster._core.instance.ref import InstanceRef
from dagster._core.types.dagster_type import Nothing
from dagster._utils import file_relative_path


class RandomAssets(NamedTuple):
    name: str
    n_assets: int
    n_roots: int = 0
    n_sources: int = 0
    asset_partitions_def: Optional[PartitionsDefinition] = None
    root_partitions_def: Optional[PartitionsDefinition] = None
    max_connectivity: int = 20

    def get_definitions(
        self, freshness_ids: AbstractSet[int] = frozenset()
    ) -> Tuple[Sequence[SourceAsset], Sequence[AssetsDefinition], AssetsDefinition]:
        """Builds a random set of assets based on the given parameters."""
        random.seed(11235711)

        deps = {
            f"asset_{i}": {
                AssetKey(f"asset_{j}")
                for j in random.sample(range(i), min(i, random.randint(1, self.max_connectivity)))
            }
            for i in range(self.n_assets)
        }

        roots = []
        for i in range(self.n_roots):

            @asset(
                partitions_def=self.root_partitions_def,
                name=f"root_{i}",
            )
            def _asset():
                pass

            deps[f"asset_{i}"].add(AssetKey(f"root_{i}"))
            roots.append(_asset)

        sources = []
        for i in range(self.n_sources):
            _source_asset = SourceAsset(key=f"source_{i}")
            for j in random.sample(
                range(self.max_connectivity), random.randint(1, self.max_connectivity)
            ):
                deps[f"asset_{j}"].add(_source_asset.key)
            sources.append(_source_asset)

        @multi_asset(
            outs={
                f"asset_{i}": AssetOut(
                    freshness_policy=FreshnessPolicy(maximum_lag_minutes=10)
                    if i in freshness_ids
                    else None,
                    dagster_type=Nothing,
                    is_required=False,
                )
                for i in range(self.n_assets)
            },
            non_argument_deps={
                *(f"root_{i}" for i in range(self.n_roots)),
                *(f"source_{i}" for i in range(self.n_sources)),
            },
            internal_asset_deps=deps,
            can_subset=True,
            partitions_def=self.asset_partitions_def,
        )
        def _masset(context):
            selected_outputs = context.selected_output_names
            # ensure topological ordering of outputs
            for i in range(self.n_roots):
                if f"root_{i}" in selected_outputs:
                    yield Output(None, f"root_{i}")
            for i in range(self.n_assets):
                if f"asset_{i}" in selected_outputs:
                    yield Output(None, f"asset_{i}")

        return sources, roots, _masset


class InstanceSnapshot(NamedTuple):
    assets: RandomAssets

    n_runs: int = 1
    randomize_runs: bool = False
    partition_keys_to_backfill: Optional[Sequence[str]] = None

    @property
    def name(self) -> str:
        if self.partition_keys_to_backfill:
            runs_str = f"{len(self.partition_keys_to_backfill)}_partition_keys"
        else:
            runs_str = (
                f"{self.n_runs}_random_runs" if self.randomize_runs else f"{self.n_runs}_runs"
            )
        return f"{self.assets.name}_{runs_str}"

    @property
    def path(self) -> str:
        return file_relative_path(__file__, f"snapshots/{self.name}.tar.gz")

    def create(self: "InstanceSnapshot") -> None:
        """Executes the specified runs for the given asset graph, writing the resulting instance to
        the snapshot directory.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            with DagsterInstance.from_ref(InstanceRef.from_dir(temp_dir)) as instance:
                sources, roots, multi_asset = self.assets.get_definitions()
                if self.assets.root_partitions_def:
                    for partition_key in self.partition_keys_to_backfill or []:
                        materialize_to_memory(
                            roots,
                            instance=instance,
                            partition_key=partition_key,
                        )

                if self.assets.asset_partitions_def:
                    for partition_key in self.partition_keys_to_backfill or []:
                        materialize_to_memory(
                            [multi_asset],
                            instance=instance,
                            partition_key=partition_key,
                        )
                else:
                    asset_graph = AssetGraph.from_assets([*sources, *roots, multi_asset])
                    for i in range(self.n_runs):
                        if self.randomize_runs:
                            target_asset = random.randint(0, self.assets.n_assets)
                            selection = AssetSelection.keys(
                                AssetKey(f"asset_{target_asset}")
                            ).upstream()
                            # don't select root assets if they're partitioned
                            if self.assets.n_roots > 0 and self.assets.root_partitions_def:
                                selection = selection - AssetSelection.keys(
                                    *(f"root_{i}" for i in range(self.assets.n_roots))
                                )

                            selected_keys = selection.resolve(asset_graph)
                            sampled_multi_asset = multi_asset.subset_for(selected_keys)
                            sampled_roots = [ra for ra in roots if ra.key in selected_keys]
                            to_materialize = [*sampled_roots, sampled_multi_asset]
                        else:
                            to_materialize = (
                                [*roots, multi_asset]
                                if not self.assets.root_partitions_def
                                else [multi_asset]
                            )

                        materialize_to_memory(to_materialize, instance=instance)

            # write as a compressed file
            with tarfile.open(self.path, "w:gz") as tf:
                for fname in os.listdir(temp_dir):
                    tf.add(os.path.join(temp_dir, fname), arcname=fname)


class PerfScenario(NamedTuple):
    snapshot: InstanceSnapshot
    n_freshness_policies: int
    max_execution_time_seconds: int

    @property
    def name(self) -> str:
        return f"{self.snapshot.name}_{self.n_freshness_policies}_freshness_policies"

    def get_repository(
        self,
    ) -> RepositoryDefinition:
        random.seed(123123123)

        @repository
        def repo():
            return list(
                self.snapshot.assets.get_definitions(
                    freshness_ids=set(
                        random.sample(
                            range(self.snapshot.assets.n_assets), self.n_freshness_policies
                        )
                    )
                )
            )

        return repo

    def do_scenario(self: "PerfScenario"):
        if not os.path.exists(self.snapshot.path):
            self.snapshot.create()

        repo = self.get_repository()
        with tempfile.TemporaryDirectory() as temp_dir, tarfile.open(self.snapshot.path) as tf:
            tf.extractall(temp_dir)
            with DagsterInstance.from_ref(InstanceRef.from_dir(temp_dir)) as instance:
                sensor = build_asset_reconciliation_sensor(asset_selection=AssetSelection.all())
                start = time.time()
                sensor.evaluate_tick(
                    build_sensor_context(
                        instance=instance,
                        repository_def=repo,
                    )
                )
                end = time.time()
                execution_time_seconds = end - start
                assert execution_time_seconds < self.max_execution_time_seconds


# ==============================================
# Instance Snapshots
#
# Note: Generating snapshots from scratch can be a very slow process, especially when giant asset
# graphs or many partitions are involved. If you add another snapshot, make sure to check it in
# once it's been generated.
# ==============================================

# 2000 assets, no partitions
unpartitioned_2000_assets = RandomAssets(
    name="giant_unpartitioned_assets", n_assets=2000, n_sources=500
)
unpartitioned_2000_assets_1_run = InstanceSnapshot(assets=unpartitioned_2000_assets)
unpartitioned_2000_assets_2_random_runs = InstanceSnapshot(
    assets=unpartitioned_2000_assets,
    n_runs=2,
    randomize_runs=True,
)

# 2000 assets, roots are daily partitioned
root_partitioned_2000_assets_1_run = InstanceSnapshot(
    assets=RandomAssets(
        name="giant_root_daily_partitioned_assets",
        n_assets=2000,
        n_roots=500,
        root_partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
    ),
    partition_keys_to_backfill=["2020-01-01"],
)

# 500 assets, no partitions
unpartitioned_500_assets_2_random_runs = InstanceSnapshot(
    assets=RandomAssets(name="large_unpartitioned_assets", n_assets=500, n_sources=100),
    n_runs=2,
    randomize_runs=True,
)

# 500 assets, all daily partitioned
all_daily_partitioned_500_assets = RandomAssets(
    name="large_all_daily_partitioned_assets",
    n_assets=500,
    asset_partitions_def=DailyPartitionsDefinition(start_date="2020-01-01"),
)
all_daily_partitioned_500_assets_2_partition_keys = InstanceSnapshot(
    assets=all_daily_partitioned_500_assets,
    partition_keys_to_backfill=["2020-01-01", "2020-01-02"],
)
all_daily_partitioned_500_assets_20_partition_keys = InstanceSnapshot(
    assets=all_daily_partitioned_500_assets,
    partition_keys_to_backfill=[f"2020-01-{i+1:02}" for i in range(20)],
)

# 100 assets, all hourly partitioned
hourly_partitions_def = HourlyPartitionsDefinition(start_date="2020-01-01-00:00")
all_hourly_partitioned_100_assets = RandomAssets(
    name="all_hourly_partitioned_100_assets",
    n_assets=100,
    asset_partitions_def=hourly_partitions_def,
)
all_hourly_partitioned_100_assets_2_partition_keys = InstanceSnapshot(
    assets=all_hourly_partitioned_100_assets,
    partition_keys_to_backfill=["2020-01-01-00:00", "2020-01-02-00:00"],
)
all_hourly_partitioned_100_assets_100_partition_keys = InstanceSnapshot(
    assets=all_hourly_partitioned_100_assets,
    partition_keys_to_backfill=hourly_partitions_def.get_partition_keys_in_range(
        PartitionKeyRange("2020-01-01-00:00", "2020-01-05-03:00")
    ),
)


# ==============================================
# Scenarios
# ==============================================
perf_scenarios = [
    PerfScenario(
        snapshot=unpartitioned_2000_assets_1_run,
        n_freshness_policies=0,
        max_execution_time_seconds=10,
    ),
    PerfScenario(
        snapshot=unpartitioned_2000_assets_1_run,
        n_freshness_policies=10,
        max_execution_time_seconds=20,
    ),
    PerfScenario(
        snapshot=unpartitioned_2000_assets_1_run,
        n_freshness_policies=100,
        max_execution_time_seconds=25,
    ),
    PerfScenario(
        snapshot=unpartitioned_2000_assets_2_random_runs,
        n_freshness_policies=0,
        max_execution_time_seconds=10,
    ),
    PerfScenario(
        snapshot=unpartitioned_2000_assets_2_random_runs,
        n_freshness_policies=10,
        max_execution_time_seconds=25,
    ),
    PerfScenario(
        snapshot=unpartitioned_500_assets_2_random_runs,
        n_freshness_policies=0,
        max_execution_time_seconds=5,
    ),
    PerfScenario(
        snapshot=unpartitioned_500_assets_2_random_runs,
        n_freshness_policies=100,
        max_execution_time_seconds=10,
    ),
    PerfScenario(
        snapshot=all_daily_partitioned_500_assets_2_partition_keys,
        n_freshness_policies=100,
        max_execution_time_seconds=15,
    ),
    PerfScenario(
        snapshot=all_hourly_partitioned_100_assets_2_partition_keys,
        n_freshness_policies=100,
        max_execution_time_seconds=30,
    ),
]


@pytest.mark.parametrize("scenario", perf_scenarios, ids=[s.name for s in perf_scenarios])
def test_reconciliation_perf(scenario: PerfScenario):
    if os.getenv("BUILDKITE") is not None and scenario.max_execution_time_seconds > 30:
        pytest.skip("Skipping slow test on BK")

    scenario.do_scenario()
