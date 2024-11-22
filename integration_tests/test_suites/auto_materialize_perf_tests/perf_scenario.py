import os
import random
import tarfile
import tempfile
import warnings
from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime
from typing import NamedTuple, Optional

from dagster import (
    AssetKey,
    AssetOut,
    AssetSelection,
    AutoMaterializePolicy,
    DagsterInstance,
    Definitions,
    ExperimentalWarning,
    Nothing,
    Output,
    PartitionsDefinition,
    RunRequest,
    SourceAsset,
    materialize,
    multi_asset,
)
from dagster._core.instance.ref import InstanceRef
from dagster._core.storage.partition_status_cache import get_and_update_asset_status_cache_value
from dagster._utils import file_relative_path

warnings.simplefilter("ignore", category=ExperimentalWarning)


class ActivityHistory(NamedTuple):
    """Represents a history of activity that happened on the instance."""

    run_requests: Sequence[RunRequest]

    def play_history(self, defs: Definitions, instance: DagsterInstance) -> None:
        asset_graph = defs.get_asset_graph()

        for run_request in self.run_requests:
            materialize(
                asset_graph.assets_defs,
                instance=instance,
                selection=run_request.asset_selection,
                partition_key=run_request.partition_key,
                tags=run_request.tags,
            )

        for asset_key in list(asset_graph.materializable_asset_keys):
            get_and_update_asset_status_cache_value(
                instance, asset_key, asset_graph.get(asset_key).partitions_def
            )


class PerfScenario(NamedTuple):
    name: str
    defs: Definitions
    activity_history: ActivityHistory
    max_execution_time_seconds: int
    current_time: Optional[datetime] = None

    def save_instance_snapshot(self) -> None:
        """Executes the specified runs for the given asset graph, writing the resulting instance to
        the snapshot directory.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            with DagsterInstance.from_ref(InstanceRef.from_dir(temp_dir)) as instance:
                self.activity_history.play_history(self.defs, instance)

            # write as a compressed file
            with tarfile.open(self.instance_snapshot_path, "w:gz") as tf:
                for fname in os.listdir(temp_dir):
                    tf.add(os.path.join(temp_dir, fname), arcname=fname)

    @contextmanager
    def instance_from_snapshot(self):
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            tarfile.open(self.instance_snapshot_path) as tf,
        ):
            tf.extractall(temp_dir)
            with DagsterInstance.from_ref(InstanceRef.from_dir(temp_dir)) as instance:
                yield instance

    @property
    def instance_snapshot_path(self) -> str:
        return file_relative_path(__file__, f"snapshots/{self.name}.tar.gz")


class RandomAssets(NamedTuple):
    name: str
    n_assets: int
    n_sources: int = 0
    asset_partitions_def: Optional[PartitionsDefinition] = None
    max_connectivity: int = 20

    def build_definitions(self) -> Definitions:
        """Builds a random set of assets based on the given parameters."""
        random.seed(11235711)

        deps = {
            f"asset_{i}": {
                AssetKey(f"asset_{j}")
                for j in random.sample(range(i), min(i, random.randint(1, self.max_connectivity)))
            }
            for i in range(self.n_assets)
        }

        sources: list[SourceAsset] = []
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
                    dagster_type=Nothing,
                    is_required=False,
                    auto_materialize_policy=AutoMaterializePolicy.eager(),
                )
                for i in range(self.n_assets)
            },
            deps=[*(f"source_{i}" for i in range(self.n_sources))],
            internal_asset_deps=deps,
            can_subset=True,
            partitions_def=self.asset_partitions_def,
        )
        def _masset(context):
            selected_outputs = context.selected_output_names
            # ensure topological ordering of outputs
            for i in range(self.n_assets):
                if f"asset_{i}" in selected_outputs:
                    yield Output(None, f"asset_{i}")

        return Definitions(assets=[*sources, _masset])

    def build_scenario(
        self,
        max_execution_time_seconds: int,
        n_runs: int = 1,
        randomize_runs: bool = False,
        partition_keys_to_backfill: Optional[Sequence[str]] = None,
    ) -> PerfScenario:
        defs = self.build_definitions()
        asset_graph = defs.get_asset_graph()

        run_requests: list[RunRequest] = []

        if self.asset_partitions_def:
            for partition_key in partition_keys_to_backfill or []:
                run_requests.append(
                    RunRequest(
                        asset_selection=list(asset_graph.materializable_asset_keys),
                        partition_key=partition_key,
                    )
                )
        else:
            for i in range(n_runs):
                if randomize_runs:
                    target_asset = random.randint(0, self.n_assets)
                    selection = AssetSelection.keys(AssetKey(f"asset_{target_asset}")).upstream()
                    to_materialize = selection.resolve(asset_graph)
                else:
                    to_materialize = asset_graph.materializable_asset_keys

                run_requests.append(RunRequest(asset_selection=list(to_materialize)))

        if partition_keys_to_backfill:
            runs_str = f"{len(partition_keys_to_backfill)}_partition_keys"
        else:
            runs_str = f"{n_runs}_random_runs" if randomize_runs else f"{n_runs}_runs"
        name = f"{self.name}_{runs_str}"

        return PerfScenario(
            defs=defs,
            activity_history=ActivityHistory(run_requests),
            max_execution_time_seconds=max_execution_time_seconds,
            name=name,
        )
