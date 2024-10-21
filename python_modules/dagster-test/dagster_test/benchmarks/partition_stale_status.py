# ruff: noqa: T201
import argparse
from random import randint
from typing import Sequence, Union

from dagster import StaticPartitionsDefinition, asset
from dagster._core.asset_graph_view.asset_graph_view import AssetGraphView, TemporalContext
from dagster._core.definitions.asset_graph import AssetGraph
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.data_version import (
    SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD,
    CachingStaleStatusResolver,
    StaleStatus,
)
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.instance import DagsterInstance
from dagster._core.instance_for_test import instance_for_test
from dagster._core.storage.tags import (
    ASSET_PARTITION_RANGE_END_TAG,
    ASSET_PARTITION_RANGE_START_TAG,
)
from dagster._time import get_current_datetime
from dagster._utils.test.data_versions import materialize_asset

from dagster_test.utils.benchmark import ProfilingSession

DESC = """
Analyze execution time when materializing and resolving stale status for assets in a graph with
a single partitioned root asset. The asset graph looks like this:

    [N partitions]     [unpartitioned]            [unpartitioned]
    (root) ----------> (downstream1)  ----------> (downstream2)

N is configurable via the `--num-partitions` arg. The script executes a sequence of materializations
and stale status resolution checks divided into discrete steps. Execution time is logged for each
step.

If `--override-partition-limit` is True (this is the default), then the
`SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD` is set to N before executing the benchmark
sequence. This allows local profiling for large numbers of dependencies without the
optimizations/compromises we currently use in the shipped `dagster` package, where we don't attempt
to accurately compute data versions or resolve stale status for partitioned dependencies that exceed
this limit.
"""

parser = argparse.ArgumentParser(
    prog="partition_staleness",
    description=DESC,
)

parser.add_argument(
    "--num-partitions",
    type=int,
    default=SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD - 1,
    help=(
        "Set the number of partitions in `root` asset. Defaults to"
        " `SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD`-1, which means the benchmark will test"
        " the maximum number of upstream partitions Dagster will tolerate when attempting to"
        " accurately compute staleness (exceeding this threshold means Dagster skips staleness"
        " calculation)."
    ),
)

parser.add_argument(
    "--override-partition-limit",
    action=argparse.BooleanOptionalAction,  # type: ignore  # (3.9+ only)
    default=True,
    help=(
        "Override the `SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD` with the value of"
        " `--num-partitions`."
    ),
)

# ########################
# ##### DEFINITIONS
# ########################


def get_stale_status_resolver(
    instance: DagsterInstance,
    assets: Sequence[Union[AssetsDefinition, SourceAsset]],
) -> CachingStaleStatusResolver:
    asset_graph = AssetGraph.from_assets(assets)
    asset_graph_view = AssetGraphView(
        temporal_context=TemporalContext(effective_dt=get_current_datetime(), last_event_id=None),
        instance=instance,
        asset_graph=asset_graph,
    )
    return CachingStaleStatusResolver(
        instance=instance,
        asset_graph=AssetGraph.from_assets(assets),
        loading_context=asset_graph_view,
    )


# ########################
# ##### MAIN
# ########################


def main(num_partitions: int, override_partition_limit: bool) -> None:
    if override_partition_limit:
        override_value = num_partitions + 1
        print(f"Setting partition limit at {override_value}")

        # We need to separately patch this in every module where it's used.
        import dagster._core.definitions.data_version
        import dagster._core.execution.context.system

        for module in [
            dagster._core.definitions.data_version,  # noqa: SLF001
            dagster._core.execution.context.system,  # noqa: SLF001
        ]:
            setattr(module, "SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD", override_value)
        partition_limit = override_value
    else:
        partition_limit = SKIP_PARTITION_DATA_VERSION_DEPENDENCY_THRESHOLD

    partitions_def = StaticPartitionsDefinition([str(x) for x in range(num_partitions)])

    @asset(partitions_def=partitions_def)
    def root(context):
        keys = partitions_def.get_partition_keys_in_range(context.partition_key_range)
        return {key: randint(0, 100) for key in keys}

    @asset
    def downstream1(root): ...

    @asset
    def downstream2(downstream1): ...

    all_assets = [root, downstream1, downstream2]
    with instance_for_test() as instance:
        session = ProfilingSession(
            name="Partition stale status",
            experiment_settings={
                "num_partitions": num_partitions,
                "override_partition_limit": override_partition_limit,
            },
        ).start()

        session.log_start_message()

        with session.logged_execution_time("Resolve StaleStatus of all assets"):
            status_resolver = get_stale_status_resolver(instance, all_assets)
            for partition_key in partitions_def.get_partition_keys():
                assert status_resolver.get_status(root.key, partition_key) == StaleStatus.MISSING
            assert status_resolver.get_status(downstream1.key) == StaleStatus.MISSING
            assert status_resolver.get_status(downstream2.key) == StaleStatus.MISSING

        with session.logged_execution_time(
            f"Materialize all {num_partitions} partitions of `root`"
        ):
            materialize_asset(
                all_assets,
                root,
                instance,
                tags={
                    ASSET_PARTITION_RANGE_START_TAG: "0",
                    ASSET_PARTITION_RANGE_END_TAG: str(num_partitions - 1),
                },
            )

        with session.logged_execution_time("Materialize `downstream1`"):
            materialize_asset(all_assets, downstream1, instance)

        with session.logged_execution_time("Resolve StaleStatus of all assets"):
            status_resolver = get_stale_status_resolver(instance, all_assets)
            for partition_key in partitions_def.get_partition_keys():
                assert status_resolver.get_status(root.key, partition_key) == StaleStatus.FRESH
            assert status_resolver.get_status(downstream1.key) == StaleStatus.FRESH
            assert status_resolver.get_status(downstream2.key) == StaleStatus.MISSING

        with session.logged_execution_time("Materialize `downstream2`"):
            materialize_asset(all_assets, downstream2, instance)

        with session.logged_execution_time("Resolve StaleStatus of all assets"):
            status_resolver = get_stale_status_resolver(instance, all_assets)
            for partition_key in partitions_def.get_partition_keys():
                assert status_resolver.get_status(root.key, partition_key) == StaleStatus.FRESH
            assert status_resolver.get_status(downstream1.key) == StaleStatus.FRESH
            assert status_resolver.get_status(downstream2.key) == StaleStatus.FRESH

        with session.logged_execution_time("Materialize single partition of `root`"):
            materialize_asset(all_assets, root, instance, partition_key="0")

        with session.logged_execution_time("Resolve StaleStatus of all assets"):
            status_resolver = get_stale_status_resolver(instance, all_assets)
            for partition_key in partitions_def.get_partition_keys():
                assert status_resolver.get_status(root.key, partition_key) == StaleStatus.FRESH

            # Status depends on whether we've exceeded the partition limit-- if yes, then downstream
            # assets will be fresh despite the fact that upstream data has changed, because we don't
            # look for the change when there are too many upstream partitions.
            target_status = (
                StaleStatus.FRESH if num_partitions >= partition_limit else StaleStatus.STALE
            )
            assert status_resolver.get_status(downstream1.key) == target_status
            assert status_resolver.get_status(downstream2.key) == target_status

        session.log_result_summary()


if __name__ == "__main__":
    args = parser.parse_args()
    main(args.num_partitions, args.override_partition_limit)
