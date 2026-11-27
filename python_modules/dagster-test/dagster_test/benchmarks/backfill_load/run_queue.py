# ruff: noqa: T201
r"""Load test for the queued run coordinator daemon.

Fills run storage with --active in-progress runs and --queued queued runs, then runs daemon
iterations until every queued run is launched, reporting the launch rate. For example, to check
the target of launching 1000 runs per second while 50,000 runs are in progress:

    python -m dagster_test.benchmarks.backfill_load.run_queue \
        --postgres-url postgresql://test:test@localhost:5432/test \
        --active 50000 --queued 10000 --workers 64
"""

import argparse
import cProfile
import logging
import time
from collections.abc import Sequence

from dagster._core.storage.dagster_run import DagsterRunStatus, RunsFilter
from dagster._core.storage.tags import BACKFILL_ID_TAG
from dagster._core.test_utils import create_test_daemon_workspace_context
from dagster._core.workspace.load_target import EmptyWorkspaceTarget
from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import QueuedRunCoordinatorDaemon

from dagster_test.benchmarks.backfill_load.harness import (
    add_storage_arguments,
    bulk_insert_runs,
    load_test_instance,
)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    add_storage_arguments(parser)
    parser.add_argument("--active", type=int, default=50000, help="Runs in progress.")
    parser.add_argument("--queued", type=int, default=10000, help="Queued runs to launch.")
    parser.add_argument(
        "--workers", type=int, default=0, help="Dequeue threads. 0 dequeues on the main thread."
    )
    parser.add_argument(
        "--max-concurrent-runs", type=int, default=-1, help="Run queue limit. -1: no limit."
    )
    parser.add_argument(
        "--tag-limit",
        action="store_true",
        help="Add a tag concurrency limit that matches every run but never blocks.",
    )
    parser.add_argument("--page-size", type=int, default=100, help="Queued runs fetched per page.")
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument(
        "--profile", help="Write a cProfile of the daemon iterations (main thread only) here."
    )
    args = parser.parse_args(argv)

    run_queue_config: dict = {"max_concurrent_runs": args.max_concurrent_runs}
    if args.workers:
        run_queue_config.update(dequeue_use_threads=True, dequeue_num_workers=args.workers)
    if args.tag_limit:
        run_queue_config["tag_concurrency_limits"] = [{"key": "team", "limit": 10**9}]

    with load_test_instance(args.postgres_url, args.pool_size, run_queue_config) as instance:
        # Runs submitted by backfills, the main source of large queues
        tags = {"team": "a", BACKFILL_ID_TAG: "load_test"}
        start = time.time()
        bulk_insert_runs(instance, args.active, DagsterRunStatus.STARTED, tags)
        bulk_insert_runs(instance, args.queued, DagsterRunStatus.QUEUED, tags)
        print(
            f"Inserted {args.active} active and {args.queued} queued runs"
            f" in {time.time() - start:.1f}s"
        )

        with (
            create_test_daemon_workspace_context(EmptyWorkspaceTarget(), instance) as context,
            QueuedRunCoordinatorDaemon(interval_seconds=0, page_size=args.page_size) as daemon,
        ):
            logging.getLogger("dagster").setLevel(logging.WARNING)
            profiler = cProfile.Profile() if args.profile else None
            launched_total = 0
            start = time.time()
            for i in range(args.max_iterations):
                iteration_start = time.time()
                if profiler:
                    profiler.enable()
                list(daemon.run_iteration(context))
                if profiler:
                    profiler.disable()
                duration = time.time() - iteration_start
                launched = instance.get_runs_count(RunsFilter(statuses=[DagsterRunStatus.STARTING]))
                print(
                    f"iteration {i}: {duration:.2f}s, launched {launched - launched_total}"
                    f" ({(launched - launched_total) / duration:.0f} runs/s)",
                    flush=True,
                )
                launched_total = launched
                if launched_total >= args.queued:
                    break
            elapsed = time.time() - start
            print(
                f"Launched {launched_total} runs in {elapsed:.1f}s:"
                f" {launched_total / elapsed:.0f} runs/s with {args.active} runs in progress"
            )
            if profiler:
                profiler.dump_stats(args.profile)
            if launched_total < args.queued:
                raise Exception(
                    f"Only {launched_total} of {args.queued} queued runs were launched in"
                    f" {args.max_iterations} iterations"
                )


if __name__ == "__main__":
    main()
