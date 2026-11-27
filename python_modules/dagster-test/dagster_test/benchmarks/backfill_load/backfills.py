# ruff: noqa: T201
r"""Load test for the backfill daemon.

Submits --backfills asset backfills at --arrival-rate backfills per second, each targeting every
partition of a chain of --assets daily-partitioned assets with --partitions partitions. Then
alternates backfill daemon iterations, run queue daemon iterations and a simulator that completes
launched runs, until every backfill completes. Reports per-iteration timings and the overall run
rate. For example, 1000 backfills arriving at 10 per second:

    python -m dagster_test.benchmarks.backfill_load.backfills \
        --postgres-url postgresql://test:test@localhost:5432/test \
        --backfills 1000 --arrival-rate 10 --assets 10 --partitions 10 --workers 16

--large-backfills adds backfills of a second chain of assets with --large-partitions partitions,
submitted up front, and --active inserts runs in progress that never complete, to run the
backfill daemon and the run queue under the load of a busy deployment.
"""

import argparse
import cProfile
import logging
import time
from collections import Counter
from collections.abc import Sequence
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import ExitStack

from dagster._core.definitions.asset_key import AssetKey
from dagster._core.execution.backfill import (
    BULK_ACTION_TERMINAL_STATUSES,
    BulkActionsFilter,
    BulkActionStatus,
    PartitionBackfill,
)
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.utils import make_new_backfill_id
from dagster._daemon.backfill import execute_backfill_iteration
from dagster._daemon.daemon import get_default_daemon_logger
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon

from dagster_test.benchmarks.backfill_load.definitions import (
    ASSET_PREFIX,
    LARGE_ASSET_PREFIX,
    backfill_policy,
)
from dagster_test.benchmarks.backfill_load.harness import (
    RunSimulator,
    add_storage_arguments,
    bulk_insert_runs,
    load_test_instance,
    load_test_workspace,
)

IN_PROGRESS_STATUSES = [s for s in BulkActionStatus if s not in BULK_ACTION_TERMINAL_STATUSES]


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    add_storage_arguments(parser)
    parser.add_argument("--backfills", type=int, default=1, help="Backfills to submit.")
    parser.add_argument(
        "--arrival-rate",
        type=float,
        default=0,
        help="Backfills submitted per second. 0 submits them all up front.",
    )
    parser.add_argument(
        "--large-backfills",
        type=int,
        default=0,
        help=(
            "Additional backfills, submitted up front, of every partition of a second chain of"
            " assets with --large-partitions partitions."
        ),
    )
    parser.add_argument(
        "--large-partitions",
        type=int,
        default=10000,
        help="Partitions per asset targeted by --large-backfills.",
    )
    parser.add_argument(
        "--active",
        type=int,
        default=0,
        help="Runs of another job inserted as in progress up front, which never complete.",
    )
    parser.add_argument("--assets", type=int, default=10, help="Assets in the chain.")
    parser.add_argument("--partitions", type=int, default=10000, help="Partitions per asset.")
    parser.add_argument(
        "--backfill-policy",
        default="multi1",
        help="Backfill policy of every asset: single, multi<N> or none (default: multi1).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Backfill daemon threads (num_workers). 0 iterates on the main thread.",
    )
    parser.add_argument(
        "--submit-workers",
        type=int,
        default=0,
        help="Backfill daemon run submission threads (num_submit_workers).",
    )
    parser.add_argument("--queue-workers", type=int, default=32, help="Run queue dequeue threads.")
    parser.add_argument(
        "--run-duration", type=float, default=0.0, help="Seconds a simulated run stays STARTED."
    )
    parser.add_argument("--max-iterations", type=int, default=1000)
    parser.add_argument(
        "--profile", help="Write a cProfile of the backfill iterations (main thread only) here."
    )
    args = parser.parse_args(argv)
    try:
        backfill_policy(args.backfill_policy)
    except ValueError as e:
        parser.error(str(e))
    if args.large_backfills and args.large_partitions < 1:
        parser.error("--large-backfills requires --large-partitions of at least 1")

    run_queue_config = {"dequeue_use_threads": True, "dequeue_num_workers": args.queue_workers}
    with ExitStack() as stack:
        instance = stack.enter_context(
            load_test_instance(args.postgres_url, args.pool_size, run_queue_config)
        )
        context = stack.enter_context(
            load_test_workspace(
                instance,
                args.assets,
                args.partitions,
                args.backfill_policy,
                num_large_partitions=args.large_partitions if args.large_backfills else 0,
            )
        )
        queue_daemon = stack.enter_context(QueuedRunCoordinatorDaemon(interval_seconds=0))
        executor = stack.enter_context(ThreadPoolExecutor(args.workers)) if args.workers else None
        submit_executor = (
            stack.enter_context(ThreadPoolExecutor(args.submit_workers))
            if args.submit_workers
            else None
        )
        logger = get_default_daemon_logger("BackfillDaemon")
        logging.getLogger("dagster").setLevel(logging.WARNING)

        asset_graph = context.create_request_context().asset_graph
        asset_keys = sorted(
            key
            for key in asset_graph.materializable_asset_keys
            if key.path[0].startswith(f"{ASSET_PREFIX}_")
        )
        large_asset_keys = sorted(
            key
            for key in asset_graph.materializable_asset_keys
            if key.path[0].startswith(f"{LARGE_ASSET_PREFIX}_")
        )
        partitions_def = asset_graph.get(asset_keys[0]).partitions_def
        assert partitions_def
        print(
            f"{args.backfills} backfills of {len(asset_keys)} assets x"
            f" {partitions_def.get_num_partitions()} partitions"
        )
        if args.large_backfills:
            large_partitions_def = asset_graph.get(large_asset_keys[0]).partitions_def
            assert large_partitions_def
            print(
                f"{args.large_backfills} backfills of {len(large_asset_keys)} assets x"
                f" {large_partitions_def.get_num_partitions()} partitions"
            )
            # Both chains are daily from START_DATE, so the larger partitions definition contains
            # the partitions of both: the simulator expands partition ranges with it
            partitions_def = max(
                partitions_def, large_partitions_def, key=lambda d: d.get_num_partitions()
            )
        if args.active:
            # STARTED runs of a job outside the workspace: the run queue daemon counts them as in
            # progress, but the simulator only picks up STARTING runs, so they never complete
            bulk_insert_runs(instance, args.active, DagsterRunStatus.STARTED, {})
            print(f"Inserted {args.active} runs in progress")

        def submit_backfill(keys: Sequence[AssetKey]) -> None:
            instance.add_backfill(
                PartitionBackfill.from_asset_partitions(
                    backfill_id=make_new_backfill_id(),
                    asset_graph=asset_graph,
                    partition_names=None,
                    asset_selection=keys,
                    backfill_timestamp=time.time(),
                    tags={},
                    dynamic_partitions_store=instance,
                    all_partitions=True,
                    title=None,
                    description=None,
                    run_config=None,
                )
            )

        simulator = RunSimulator(instance, partitions_def, args.run_duration)
        futures: dict[str, Future] = {}
        profiler = cProfile.Profile() if args.profile else None

        for _ in range(args.large_backfills):
            submit_backfill(large_asset_keys)
        num_backfills = args.backfills + args.large_backfills

        submitted = 0
        in_progress = 0
        start = time.time()
        backfill_time = 0.0
        max_backfill_iteration = 0.0
        for i in range(args.max_iterations):
            due = (
                min(args.backfills, int((time.time() - start) * args.arrival_rate) + 1)
                if args.arrival_rate
                else args.backfills
            )
            while submitted < due:
                submit_backfill(asset_keys)
                submitted += 1

            iteration_start = time.time()
            if profiler:
                profiler.enable()
            previous_futures = dict(futures)
            errors = list(
                execute_backfill_iteration(
                    context,
                    logger,
                    threadpool_executor=executor,
                    backfill_futures=futures,
                    submit_threadpool_executor=submit_executor,
                )
            )
            # Wait for the iterations submitted to threads so that each one is measured in full
            for backfill_id, future in futures.items():
                if previous_futures.get(backfill_id) is not future:
                    errors.extend(future.result())
            if profiler:
                profiler.disable()
            backfill_duration = time.time() - iteration_start
            backfill_time += backfill_duration
            max_backfill_iteration = max(max_backfill_iteration, backfill_duration)
            for error in errors:
                if error:
                    print(f"Backfill error: {error.to_string()[:2000]}")

            queue_start = time.time()
            list(queue_daemon.run_iteration(context))
            queue_duration = time.time() - queue_start
            started, completed = simulator.step()

            in_progress = instance.get_backfills_count(
                BulkActionsFilter(statuses=IN_PROGRESS_STATUSES)
            )
            print(
                f"iteration {i}: backfill daemon {backfill_duration:.2f}s,"
                f" run queue {queue_duration:.2f}s, launched {started}, completed {completed},"
                f" running {simulator.num_running},"
                f" backfill runs {instance.get_runs_count() - args.active},"
                f" backfills submitted {submitted + args.large_backfills}, in progress {in_progress}",
                flush=True,
            )
            # in_progress also counts the large backfills, which were all submitted up front
            if submitted == args.backfills and in_progress == 0:
                break

        elapsed = time.time() - start
        # The --active runs are not launched by backfills
        num_runs = instance.get_runs_count() - args.active
        statuses = Counter(backfill.status.value for backfill in instance.get_backfills())
        print(
            f"Done in {elapsed:.1f}s: {num_runs} backfill runs ({num_runs / elapsed:.0f} runs/s overall),"
            f" backfill daemon busy {backfill_time:.1f}s (longest iteration"
            f" {max_backfill_iteration:.1f}s), backfill statuses {dict(statuses)}"
        )
        if profiler:
            profiler.dump_stats(args.profile)
        if statuses[BulkActionStatus.COMPLETED_SUCCESS.value] != num_backfills:
            raise Exception(f"Not every backfill succeeded: {dict(statuses)}")


if __name__ == "__main__":
    main()
