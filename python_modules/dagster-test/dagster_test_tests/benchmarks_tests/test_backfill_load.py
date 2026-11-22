"""Smoke tests that keep the backfill load tests working, at a size that runs in seconds."""

from dagster_test.benchmarks.backfill_load import backfills, run_queue


def test_run_queue_load_test() -> None:
    run_queue.main(["--active", "10", "--queued", "20", "--workers", "2"])


def test_backfills_load_test() -> None:
    backfills.main(
        ["--backfills", "3", "--assets", "2", "--partitions", "4", "--workers", "2"]
        + ["--submit-workers", "2", "--backfill-policy", "multi2"]
    )


def test_mixed_backfills_load_test() -> None:
    backfills.main(
        ["--backfills", "2", "--assets", "2", "--partitions", "3", "--large-backfills", "1"]
        + ["--large-partitions", "6", "--active", "5", "--workers", "2", "--submit-workers", "2"]
    )
