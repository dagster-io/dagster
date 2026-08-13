"""Tests for the mid-run debug-log parser used by monitor_runs.

The parser turns dbt Cloud's stringly-typed progress logs into typed events.
These tests pin the regex to real-looking dbt output so schema changes on the
dbt or adapter side surface as regressions here (rather than silently producing
zero events at runtime).
"""

from dagster_dbt.cloud_v2.run_monitor import (
    ParsedLogKind,
    _short_name,
    collect_step_debug_logs,
    parse_debug_logs,
    strip_ansi,
)


def test_strip_ansi_removes_color_codes():
    """Dbt Cloud debug logs come colorized; the parser needs to see clean text
    or regex anchors don't fire.
    """
    text = "\x1b[32m1 of 4 OK created sql table model dev.stg_customers\x1b[0m .........."
    assert "\x1b" not in strip_ansi(text)
    assert "1 of 4 OK" in strip_ansi(text)


def test_short_name_pulls_last_dotted_segment():
    """Dbt logs schema-qualified names (``DEV.STG_CUSTOMERS``) but Dagster keys off
    the model name only. Extract the last segment so downstream unique_id lookup
    works.
    """
    assert _short_name("DEV.STG_CUSTOMERS") == "STG_CUSTOMERS"
    assert _short_name("analytics.dev.stg_orders") == "stg_orders"
    assert _short_name("bare_name") == "bare_name"


def test_parse_debug_logs_model_ok():
    """A successful model line produces one MODEL_OK event with the short name."""
    log = "1 of 4 OK created sql table model DEV.STG_CUSTOMERS .......... [SUCCESS 1 in 0.10s]"
    results = list(parse_debug_logs(log))
    assert len(results) == 1
    assert results[0].kind == ParsedLogKind.MODEL_OK
    assert results[0].name == "STG_CUSTOMERS"


def test_parse_debug_logs_model_error():
    """A failed model line produces a MODEL_ERROR event. This is what drives
    `fail_fast` cancellation and downstream alerts.
    """
    log = "2 of 4 ERROR creating sql view model dev.stg_orders ........... [ERROR in 0.11s]"
    results = list(parse_debug_logs(log))
    assert len(results) == 1
    assert results[0].kind == ParsedLogKind.MODEL_ERROR
    assert results[0].name == "stg_orders"
    assert results[0].kind.is_failure


def test_parse_debug_logs_model_skip():
    """Skipped models (upstream failed) produce a MODEL_SKIP event — not a failure,
    but also not a materialization. We surface it so users can see what didn't run.
    """
    log = "3 of 4 SKIP relation dev.stg_products ......................... [SKIP]"
    results = list(parse_debug_logs(log))
    assert len(results) == 1
    assert results[0].kind == ParsedLogKind.MODEL_SKIP
    assert not results[0].kind.is_failure


def test_parse_debug_logs_test_pass_and_fail():
    """Tests emit PASS/FAIL/WARN events; asset checks are keyed off these."""
    log = (
        "1 of 4 PASS not_null_customers_id ............................ [PASS in 0.10s]\n"
        "2 of 4 FAIL not_null_orders_id ................................ [FAIL 1 in 0.11s]\n"
        "3 of 4 WARN unique_customers_email ............................ [WARN 1 in 0.10s]\n"
    )
    results = list(parse_debug_logs(log))
    kinds = [r.kind for r in results]
    assert kinds == [ParsedLogKind.TEST_PASS, ParsedLogKind.TEST_FAIL, ParsedLogKind.TEST_WARN]
    assert results[1].kind.is_failure
    assert not results[2].kind.is_failure  # WARN is not a hard failure — matches dbt


def test_parse_debug_logs_ignores_non_terminal_lines():
    """START lines and pre-status output are informational, not terminal. Parsing
    them would produce duplicate materializations, so we skip everything except
    the terminal status words.
    """
    log = (
        "1 of 4 START sql view model dev.stg_customers ... [RUN]\n"
        "Concurrency: 4 threads (target='dev')\n"
        "Finished running 4 view models\n"
    )
    assert list(parse_debug_logs(log)) == []


def test_parse_debug_logs_ansi_colored_input():
    """Full end-to-end: ANSI-colored input still parses correctly. dbt Cloud
    debug logs always come colorized so this is the common case.
    """
    log = (
        "\x1b[32m1 of 2 OK created sql table model dev.customers\x1b[0m .......... "
        "[SUCCESS 1 in 0.10s]\n"
        "\x1b[31m2 of 2 ERROR creating sql view model dev.orders\x1b[0m ........... "
        "[ERROR in 0.11s]"
    )
    results = list(parse_debug_logs(log))
    assert [r.kind for r in results] == [ParsedLogKind.MODEL_OK, ParsedLogKind.MODEL_ERROR]
    assert [r.name for r in results] == ["customers", "orders"]


def test_parse_debug_logs_multiple_lines_all_matched():
    """When logs contain multiple terminal events, all are emitted in order."""
    log = (
        "1 of 3 OK created sql table model dev.a .......... [SUCCESS 1 in 0.10s]\n"
        "2 of 3 OK created sql table model dev.b .......... [SUCCESS 1 in 0.10s]\n"
        "3 of 3 OK created sql table model dev.c .......... [SUCCESS 1 in 0.10s]"
    )
    results = list(parse_debug_logs(log))
    assert [r.name for r in results] == ["a", "b", "c"]


def test_parse_debug_logs_deduplication_is_callers_responsibility():
    """The parser does NOT dedupe — it emits every match in order. Callers polling
    an incrementally-growing log MUST dedupe by ``(kind_category, name)`` themselves,
    because a single parser call has no state across polls.
    """
    log = (
        "1 of 2 OK created sql table model dev.a .......... [SUCCESS 1 in 0.10s]\n"
        "1 of 2 OK created sql table model dev.a .......... [SUCCESS 1 in 0.10s]"  # dup
    )
    results = list(parse_debug_logs(log))
    assert len(results) == 2  # both are emitted; caller must dedupe


def test_collect_step_debug_logs_concatenates_across_steps():
    """A dbt Cloud run has multiple `run_steps` (one per CLI invocation, e.g. `dbt run`
    then `dbt test`). The monitor loop needs the concatenation so a single parse pass
    sees the whole run's progress.
    """
    run_details = {
        "run_steps": [
            {"id": 1, "debug_logs": "step1-line1\nstep1-line2"},
            {"id": 2, "debug_logs": "step2-line1"},
            {"id": 3, "debug_logs": None},  # step not yet started
        ],
    }
    result = collect_step_debug_logs(run_details)
    assert "step1-line1" in result
    assert "step1-line2" in result
    assert "step2-line1" in result


def test_collect_step_debug_logs_empty_run_steps():
    """A run with no steps yet (still queued) returns empty string — safe to pass
    to the parser (which yields no results).
    """
    assert collect_step_debug_logs({}) == ""
    assert collect_step_debug_logs({"run_steps": []}) == ""
    assert collect_step_debug_logs({"run_steps": None}) == ""


# ============================================================================
# monitor_run_iter integration tests (poll -> parse -> emit)
# ============================================================================

from unittest.mock import MagicMock

import dagster as dg
import pytest
from dagster_dbt.cloud_v2.run_monitor import (
    find_model_unique_id_by_name,
    find_test_unique_id_by_name,
    monitor_run_iter,
)
from dagster_dbt.cloud_v2.types import DbtCloudJobRunStatusType
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator


def _manifest_with_models(model_names: list[str], test_names: list[str] | None = None) -> dict:
    """Build a minimal dbt manifest with the given model + test unique_ids."""
    nodes = {}
    for name in model_names:
        uid = f"model.pkg.{name}"
        nodes[uid] = {
            "resource_type": "model",
            "package_name": "pkg",
            "path": f"{name}.sql",
            "original_file_path": f"models/{name}.sql",
            "unique_id": uid,
            "fqn": ["pkg", name],
            "name": name,
            "config": {"enabled": True, "materialized": "table"},
            "tags": [],
            "depends_on": {"nodes": []},
            "description": "",
        }
    for name in test_names or []:
        uid = f"test.pkg.{name}"
        nodes[uid] = {
            "resource_type": "test",
            "package_name": "pkg",
            "path": f"tests/{name}.sql",
            "original_file_path": f"tests/{name}.sql",
            "unique_id": uid,
            "fqn": ["pkg", name],
            "name": name,
            "config": {"enabled": True, "materialized": "test"},
            "tags": [],
            "depends_on": {"nodes": [f"model.pkg.{model_names[0]}"]}
            if model_names
            else {"nodes": []},
            "description": "",
            "attached_node": f"model.pkg.{model_names[0]}" if model_names else None,
        }
    return {
        "metadata": {"dbt_schema_version": "1.0.0", "adapter_type": "postgres"},
        "nodes": nodes,
        "sources": {},
        "metrics": {},
        "semantic_models": {},
        "exposures": {},
        "child_map": {uid: [] for uid in nodes},
        "parent_map": {uid: [] for uid in nodes},
        "selectors": {},
    }


def test_find_model_unique_id_by_name_case_insensitive():
    """Snowflake logs uppercase names; manifests store the source-file case. The
    lookup must not care about case, otherwise Snowflake users get zero matches.
    """
    manifest = _manifest_with_models(["stg_customers", "stg_orders"])
    assert find_model_unique_id_by_name(manifest, "STG_CUSTOMERS") == "model.pkg.stg_customers"
    assert find_model_unique_id_by_name(manifest, "stg_orders") == "model.pkg.stg_orders"
    assert find_model_unique_id_by_name(manifest, "not_a_model") is None


def test_find_test_unique_id_by_name_case_insensitive():
    """Same case-insensitivity for tests."""
    manifest = _manifest_with_models(["customers"], test_names=["not_null_customers_id"])
    assert (
        find_test_unique_id_by_name(manifest, "NOT_NULL_CUSTOMERS_ID")
        == "test.pkg.not_null_customers_id"
    )


def _mock_client_with_run(final_status: int, logs_stream: list[str]):
    """Build a mock dbt Cloud client that returns pre-canned run details across
    successive `get_run_details` calls. Each call returns the next log snapshot
    from `logs_stream`; the last snapshot is paired with `final_status`.
    """
    client = MagicMock()
    responses = []
    for i, snapshot in enumerate(logs_stream):
        is_last = i == len(logs_stream) - 1
        status = final_status if is_last else DbtCloudJobRunStatusType.RUNNING.value
        responses.append(
            {
                "id": 1,
                "status": status,
                "href": f"https://cloud.getdbt.com/runs/1?snapshot={i}",
                "run_steps": [{"id": 100 + i, "debug_logs": snapshot}],
            }
        )
    client.get_run_details.side_effect = responses
    client.cancel_run.return_value = {}
    return client


def test_monitor_run_iter_emits_materialization_per_model_ok():
    """A run with one MODEL_OK per poll yields one AssetMaterialization per model.
    Dedup ensures repeated log lines across polls don't emit duplicates.
    """
    logs = [
        "1 of 2 OK created sql table model dev.stg_customers .......... [SUCCESS 1 in 0.10s]",
        (
            "1 of 2 OK created sql table model dev.stg_customers .......... [SUCCESS 1 in 0.10s]\n"
            "2 of 2 OK created sql table model dev.stg_orders .......... [SUCCESS 1 in 0.10s]"
        ),
    ]
    manifest = _manifest_with_models(["stg_customers", "stg_orders"])
    client = _mock_client_with_run(
        final_status=DbtCloudJobRunStatusType.SUCCESS.value, logs_stream=logs
    )

    events = list(
        monitor_run_iter(
            run_id=1,
            client=client,
            manifest=manifest,
            translator=DagsterDbtTranslator(),
            context=None,
            fail_fast=False,
            poll_interval=0,  # no sleep in tests
        )
    )
    mats = [e for e in events if isinstance(e, dg.AssetMaterialization)]
    assert len(mats) == 2  # deduplication: each model materialized once
    names = {mat.asset_key.to_user_string() for mat in mats}
    assert names == {"stg_customers", "stg_orders"}


def test_monitor_run_iter_raises_failure_on_terminal_error():
    """When the Cloud run ends with ERROR status, the iterator yields partial
    materializations then raises `Failure` — matches OOTB semantics.
    """
    logs = [
        (
            "1 of 2 OK created sql table model dev.stg_customers .......... [SUCCESS 1 in 0.10s]\n"
            "2 of 2 ERROR creating sql view model dev.stg_orders ........... [ERROR in 0.11s]"
        ),
    ]
    manifest = _manifest_with_models(["stg_customers", "stg_orders"])
    client = _mock_client_with_run(
        final_status=DbtCloudJobRunStatusType.ERROR.value, logs_stream=logs
    )

    events = []
    with pytest.raises(dg.Failure) as excinfo:
        for e in monitor_run_iter(
            run_id=1,
            client=client,
            manifest=manifest,
            translator=DagsterDbtTranslator(),
            context=None,
            fail_fast=False,
            poll_interval=0,
        ):
            events.append(e)
    # Partial: the OK model was materialized before the raise.
    mats = [e for e in events if isinstance(e, dg.AssetMaterialization)]
    assert [mat.asset_key.to_user_string() for mat in mats] == ["stg_customers"]
    assert "ERROR" in str(excinfo.value) or "error" in str(excinfo.value).lower()


def test_monitor_run_iter_fail_fast_cancels_on_first_error():
    """`fail_fast=True`: on the first MODEL_ERROR seen mid-run, cancel the Cloud
    run and raise immediately — even though the run itself may still be RUNNING.
    """
    logs = [
        (
            "1 of 2 OK created sql table model dev.stg_customers .......... [SUCCESS 1 in 0.10s]\n"
            "2 of 2 ERROR creating sql view model dev.stg_orders ........... [ERROR in 0.11s]"
        ),
        # This second snapshot never gets consumed because we cancel first.
        "should not be reached",
    ]
    manifest = _manifest_with_models(["stg_customers", "stg_orders"])
    client = _mock_client_with_run(
        # Even though we set SUCCESS as terminal, fail_fast should cancel BEFORE reaching it.
        final_status=DbtCloudJobRunStatusType.SUCCESS.value,
        logs_stream=logs,
    )

    events = []
    with pytest.raises(dg.Failure):
        for e in monitor_run_iter(
            run_id=1,
            client=client,
            manifest=manifest,
            translator=DagsterDbtTranslator(),
            context=None,
            fail_fast=True,
            poll_interval=0,
        ):
            events.append(e)
    # First model was materialized, then cancel was triggered.
    mats = [e for e in events if isinstance(e, dg.AssetMaterialization)]
    assert [mat.asset_key.to_user_string() for mat in mats] == ["stg_customers"]
    client.cancel_run.assert_called_once_with(1)


def test_monitor_run_iter_skips_unknown_model_names():
    """A dbt log line naming a model NOT in the manifest is skipped silently (with
    a warning). Otherwise a stale-manifest run would crash the whole invocation.
    """
    logs = [
        (
            "1 of 2 OK created sql table model dev.stg_customers .......... [SUCCESS 1 in 0.10s]\n"
            "2 of 2 OK created sql table model dev.completely_unknown .......... [SUCCESS 1 in 0.10s]"
        ),
    ]
    manifest = _manifest_with_models(["stg_customers"])  # unknown model is NOT here
    client = _mock_client_with_run(
        final_status=DbtCloudJobRunStatusType.SUCCESS.value, logs_stream=logs
    )
    events = list(
        monitor_run_iter(
            run_id=1,
            client=client,
            manifest=manifest,
            translator=DagsterDbtTranslator(),
            context=None,
            fail_fast=False,
            poll_interval=0,
        )
    )
    mats = [e for e in events if isinstance(e, dg.AssetMaterialization)]
    assert [mat.asset_key.to_user_string() for mat in mats] == ["stg_customers"]


def test_monitor_run_iter_polls_until_terminal_status():
    """The iterator keeps polling until the run reaches SUCCESS/ERROR/CANCELLED —
    it doesn't stop just because the log stopped growing.
    """
    logs = [
        "",  # first poll: no logs yet (run STARTING)
        "1 of 1 OK created sql table model dev.stg_customers .......... [SUCCESS 1 in 0.10s]",
    ]
    manifest = _manifest_with_models(["stg_customers"])
    client = _mock_client_with_run(
        final_status=DbtCloudJobRunStatusType.SUCCESS.value, logs_stream=logs
    )
    events = list(
        monitor_run_iter(
            run_id=1,
            client=client,
            manifest=manifest,
            translator=DagsterDbtTranslator(),
            context=None,
            fail_fast=False,
            poll_interval=0,
        )
    )
    # Two get_run_details calls (empty snapshot + final), one materialization.
    assert client.get_run_details.call_count == 2
    mats = [e for e in events if isinstance(e, dg.AssetMaterialization)]
    assert len(mats) == 1


def test_monitor_run_iter_emits_asset_check_evaluation_for_tests():
    """Test PASS lines emit AssetCheckEvaluation when there's no asset def in the
    context (ad hoc usage) — same shape as OOTB run-results-based emission.
    """
    logs = [
        "1 of 1 PASS not_null_customers_id ............................ [PASS in 0.10s]",
    ]
    manifest = _manifest_with_models(["customers"], test_names=["not_null_customers_id"])
    client = _mock_client_with_run(
        final_status=DbtCloudJobRunStatusType.SUCCESS.value, logs_stream=logs
    )
    events = list(
        monitor_run_iter(
            run_id=1,
            client=client,
            manifest=manifest,
            translator=DagsterDbtTranslator(),
            context=None,
            fail_fast=False,
            poll_interval=0,
        )
    )
    checks = [e for e in events if isinstance(e, dg.AssetCheckEvaluation)]
    assert len(checks) == 1
    assert checks[0].passed
    assert checks[0].check_name == "not_null_customers_id"
