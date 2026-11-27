import dagster as dg
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.storage.run_size import (
    estimate_run_size_bytes,
    exceeds_run_size_limit,
    get_run_size_bytes,
)

LIMIT = 50000


def test_get_run_size_bytes_ignores_system_populated_fields():
    base = DagsterRun(job_name="job", run_config={"foo": "bar"}, tags={"a": "b"})
    with_system_fields = DagsterRun(
        job_name="job",
        run_config={"foo": "bar"},
        tags={"a": "b"},
        asset_selection={dg.AssetKey(f"asset_{i}") for i in range(1000)},
        op_selection=[f"op_{i}" for i in range(1000)],
        step_keys_to_execute=[f"step_{i}" for i in range(1000)],
    )

    assert get_run_size_bytes(base) == get_run_size_bytes(with_system_fields)


def test_exceeds_run_size_limit():
    small = dg.RunRequest(run_key="small", run_config={"foo": "bar"}, tags={"a": "b"})
    oversized_config = dg.RunRequest(run_config={"foo": "x" * LIMIT})
    oversized_tags = dg.RunRequest(tags={"blob": "x" * LIMIT})

    assert not exceeds_run_size_limit(small, LIMIT)
    assert exceeds_run_size_limit(oversized_config, LIMIT)
    assert exceeds_run_size_limit(oversized_tags, LIMIT)

    # the estimate measures what run storage measures, modulo the tags the daemon adds later
    assert estimate_run_size_bytes(oversized_config) == get_run_size_bytes(
        DagsterRun(job_name="", run_config=oversized_config.run_config, tags={})
    )

    # a request close to but under the limit is left alone
    borderline = dg.RunRequest(run_config={"foo": "x" * (LIMIT - 1000)})
    assert estimate_run_size_bytes(borderline) < LIMIT
    assert not exceeds_run_size_limit(borderline, LIMIT)

    # requests whose bulk is in non-string leaves are caught too; a cheap structural walk
    # undercounts these badly, since a float costs one slot but ~18 serialized characters
    numeric = dg.RunRequest(run_config={"foo": [1.23456789012345] * 30000})
    assert estimate_run_size_bytes(numeric) >= LIMIT
    assert exceeds_run_size_limit(numeric, LIMIT)
