"""Lite-engine smoke test — the regression gate for the extraction.

Proves the in-process execution path works end to end with NO webserver,
daemon, or gRPC involved:
  1. asset materialization via `materialize(..., instance=ephemeral())`
  2. op/job execution via `job.execute_in_process()`

Run after every subsystem deletion. Exit 0 == green.
"""

import sys


def test_asset_materialization() -> None:
    from dagster import DagsterInstance, asset, materialize

    @asset
    def upstream() -> int:
        return 21

    @asset
    def downstream(upstream: int) -> int:
        return upstream * 2

    result = materialize([upstream, downstream], instance=DagsterInstance.ephemeral())
    assert result.success, "materialize did not succeed"
    assert result.output_for_node("downstream") == 42, "wrong asset output"
    print("  [ok] asset materialization -> 42")


def test_job_execution() -> None:
    from dagster import job, op

    @op
    def make_value() -> int:
        return 7

    @op
    def add_one(x: int) -> int:
        return x + 1

    @job
    def the_job():
        add_one(make_value())

    result = the_job.execute_in_process()
    assert result.success, "execute_in_process did not succeed"
    assert result.output_for_node("add_one") == 8, "wrong job output"
    print("  [ok] job.execute_in_process -> 8")


def main() -> int:
    import dagster

    print(f"dagster {dagster.__version__} @ {dagster.__file__}")
    test_asset_materialization()
    test_job_execution()
    print("SMOKE TEST GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
