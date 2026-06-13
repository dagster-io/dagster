"""Tests for SnowflakeDbtProjectComponent.

These tests focus on the logic that is unique to driving a dbt project natively on
Snowflake -- the `EXECUTE DBT PROJECT` SQL generation, fetching the manifest from
Snowflake, async submit/poll + cancellation, QUERY_TAG-based sensor de-duplication, and
translating `run_results.json` into Dagster events with INFORMATION_SCHEMA-backed metadata
at parity with dbt core / dbt Cloud -- without standing up a real dbt project or Snowflake
connection.
"""

import datetime
import json
import os
import tempfile
import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest import mock

import pytest
from dagster import (
    AssetCheckKey,
    AssetCheckResult,
    AssetKey,
    AssetMaterialization,
    MaterializeResult,
)
from dagster._core.errors import DagsterExecutionInterruptedError

# Skip the whole module if the optional `dagster-dbt` dependency is not installed.
pytest.importorskip("dagster_dbt")

import dagster_snowflake.components.dbt_project.component as comp_mod
from dagster_snowflake.components.dbt_project.component import (
    _QUERY_TAG_MARKER,
    SnowflakeDbtProjectComponent,
    _default_op_name,
    build_cancel_query_sql,
    build_dagster_query_ids_sql,
    build_dbt_project_execution_history_sql,
    build_execute_dbt_project_sql,
    build_get_dbt_log_sql,
    build_information_schema_columns_sql,
    build_information_schema_tables_sql,
    build_locate_artifacts_sql,
    build_set_query_tag_sql,
    build_show_dbt_artifacts_function_sql,
)

# ---------------------------------------------------------------------------
# SQL builders
# ---------------------------------------------------------------------------


def test_build_execute_dbt_project_sql_basic():
    sql = build_execute_dbt_project_sql("analytics.dbt.jaffle_shop", ["build"])
    assert sql == "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop ARGS='build'"


def test_build_execute_dbt_project_sql_joins_args():
    sql = build_execute_dbt_project_sql("proj", ["build", "--select", "tag:nightly"])
    assert sql == "EXECUTE DBT PROJECT proj ARGS='build --select tag:nightly'"


def test_build_execute_dbt_project_sql_escapes_single_quotes():
    # Single quotes in the args must be doubled so the Snowflake string literal stays valid.
    sql = build_execute_dbt_project_sql("proj", ["build", "--vars", "{'k': 'v'}"])
    assert sql == "EXECUTE DBT PROJECT proj ARGS='build --vars {''k'': ''v''}'"


def test_build_locate_artifacts_sql():
    sql = build_locate_artifacts_sql("01bf3f5a-010b-4d87-0000-53493abb7cce")
    assert sql == "SELECT SYSTEM$LOCATE_DBT_ARTIFACTS('01bf3f5a-010b-4d87-0000-53493abb7cce')"


def test_build_get_dbt_log_sql():
    sql = build_get_dbt_log_sql("build-q1")
    assert sql == "SELECT SYSTEM$GET_DBT_LOG('build-q1', 10000)"


def test_build_dbt_project_execution_history_sql():
    sql = build_dbt_project_execution_history_sql("ANALYTICS", "DBT", "JAFFLE")
    assert "DBT_PROJECT_EXECUTION_HISTORY" in sql
    assert "DATABASE => 'ANALYTICS'" in sql
    assert "SCHEMA => 'DBT'" in sql
    assert "OBJECT_NAME => 'JAFFLE'" in sql


def test_build_set_query_tag_sql():
    sql = build_set_query_tag_sql('{"app":"x","dagster_run_id":"r1"}')
    assert sql == 'ALTER SESSION SET QUERY_TAG = \'{"app":"x","dagster_run_id":"r1"}\''


def test_build_cancel_query_sql():
    assert build_cancel_query_sql("q1") == "SELECT SYSTEM$CANCEL_QUERY('q1')"


def test_build_dagster_query_ids_sql():
    sql = build_dagster_query_ids_sql(_QUERY_TAG_MARKER)
    assert "INFORMATION_SCHEMA.QUERY_HISTORY" in sql
    assert f"query_tag LIKE '%{_QUERY_TAG_MARKER}%'" in sql


def test_build_information_schema_tables_sql():
    sql = build_information_schema_tables_sql("DB", ["SCH1", "SCH2"])
    assert sql == (
        "SELECT table_schema, table_name, row_count FROM DB.INFORMATION_SCHEMA.TABLES "
        "WHERE table_schema IN ('SCH1', 'SCH2')"
    )


def test_build_information_schema_columns_sql():
    sql = build_information_schema_columns_sql("DB", ["SCH"])
    assert "DB.INFORMATION_SCHEMA.COLUMNS" in sql
    assert "table_schema IN ('SCH')" in sql
    assert "ORDER BY ordinal_position" in sql


def test_build_show_dbt_artifacts_function_sql():
    assert (
        build_show_dbt_artifacts_function_sql()
        == "SHOW FUNCTIONS LIKE 'SYSTEM$LOCATE_DBT_ARTIFACTS'"
    )


def test_default_op_name_sanitizes_qualified_name():
    assert _default_op_name("analytics.dbt.jaffle_shop") == "jaffle_shop"
    assert _default_op_name("my-project") == "my_project"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_component(**overrides: Any) -> SnowflakeDbtProjectComponent:
    """Construct a component instance directly, bypassing YAML resolution."""
    defaults: dict[str, Any] = dict(
        snowflake=mock.MagicMock(name="snowflake"),
        snowflake_dbt_project_name="analytics.dbt.jaffle_shop",
    )
    defaults.update(overrides)
    return SnowflakeDbtProjectComponent(**defaults)


def _ctx(**kwargs: Any) -> Any:
    """A stand-in AssetExecutionContext for unit tests (returned as ``Any``)."""
    kwargs.setdefault("run_id", "test-run-id")
    return SimpleNamespace(**kwargs)


def _connection_returning(cursor: Any, component: SnowflakeDbtProjectComponent) -> Any:
    """Wire ``component.snowflake.get_connection()`` to yield a conn backed by ``cursor``.

    The conn is configured so the async poll loop in ``_execute_and_wait`` completes
    immediately (``is_still_running`` returns ``False``).
    """
    conn = mock.MagicMock()
    conn.cursor.return_value = cursor
    conn.is_still_running.return_value = False
    cast("Any", component.snowflake).get_connection.return_value.__enter__.return_value = conn
    return conn


# ---------------------------------------------------------------------------
# State refresh / feature detection
# ---------------------------------------------------------------------------


def test_write_state_fetches_manifest_from_snowflake(tmp_path):
    component = _make_component(manifest_args=["parse"])

    cursor = mock.MagicMock()
    cursor.sfqid = "query-123"
    # The feature-detection probe (SHOW FUNCTIONS) returns a row => supported.
    cursor.fetchall.return_value = [("SYSTEM$LOCATE_DBT_ARTIFACTS",)]
    cursor.fetchone.return_value = ("snow://dbt/analytics.dbt.jaffle_shop/results/query_id_x/",)
    _connection_returning(cursor, component)

    sample_manifest = {"nodes": {}, "sources": {}}

    # Stand in for the Snowflake GET: drop a nested manifest.json into the temp dir.
    def fake_download(_cursor, _artifact_path, dest_dir):
        nested = os.path.join(dest_dir, "results", "target")
        os.makedirs(nested)
        with open(os.path.join(nested, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(sample_manifest, f)

    state_path = tmp_path / "state.json"
    with mock.patch.object(
        SnowflakeDbtProjectComponent, "_download_artifacts", side_effect=fake_download
    ):
        component.write_state_to_path(state_path)

    # The manifest fetched natively from Snowflake is cached as defs-state.
    assert json.loads(state_path.read_text()) == sample_manifest
    issued = [c.args[0] for c in cursor.execute.call_args_list]
    # The account is probed for dbt-on-Snowflake support before anything else.
    assert issued[0] == "SHOW FUNCTIONS LIKE 'SYSTEM$LOCATE_DBT_ARTIFACTS'"
    assert issued[1] == "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop ARGS='parse'"
    assert issued[2] == "SELECT SYSTEM$LOCATE_DBT_ARTIFACTS('query-123')"


def test_write_state_fails_cleanly_on_unsupported_account(tmp_path):
    component = _make_component()

    cursor = mock.MagicMock()
    cursor.fetchall.return_value = []  # SHOW FUNCTIONS finds nothing => not supported
    _connection_returning(cursor, component)

    with pytest.raises(Exception, match="dbt Projects on Snowflake"):
        component.write_state_to_path(tmp_path / "state.json")

    # We never attempted to EXECUTE on an unsupported account.
    issued = [c.args[0] for c in cursor.execute.call_args_list]
    assert all("EXECUTE DBT PROJECT" not in s for s in issued)


# ---------------------------------------------------------------------------
# Subsetting / SQL construction
# ---------------------------------------------------------------------------


def test_build_execute_sql_subsets_selection():
    """When the op is subset, the EXECUTE statement carries the dbt --select for those models."""
    component = _make_component()
    setattr(component, "get_cli_args", lambda context: ["build"])

    with mock.patch.object(
        comp_mod,
        "get_subset_selection_for_context",
        return_value=(["--select", "fqn:proj.customers"], None),
    ):
        sql = component.build_execute_sql(_ctx(), {})

    assert sql == (
        "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop ARGS='build --select fqn:proj.customers'"
    )


def test_build_execute_sql_translates_indirect_selection_override():
    """The DBT_INDIRECT_SELECTION override becomes a --indirect-selection CLI flag."""
    component = _make_component()
    setattr(component, "get_cli_args", lambda context: ["build"])

    with mock.patch.object(
        comp_mod,
        "get_subset_selection_for_context",
        return_value=(["--select", "fqn:proj.a"], "empty"),
    ):
        sql = component.build_execute_sql(_ctx(), {})

    assert sql == (
        "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop "
        "ARGS='build --select fqn:proj.a --indirect-selection empty'"
    )


def test_build_execute_sql_does_not_inject_args_marker():
    """De-dup is via QUERY_TAG now, so the EXECUTE args never carry a sentinel var."""
    component = _make_component(create_sensor=True)
    setattr(component, "get_cli_args", lambda context: ["build"])

    with mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)):
        sql = component.build_execute_sql(_ctx(), {})

    assert sql == "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop ARGS='build'"
    assert "--vars" not in sql


# ---------------------------------------------------------------------------
# Async execution + cancellation
# ---------------------------------------------------------------------------

_MODEL_ID = "model.jaffle_shop.customers"
_TEST_ID = "test.jaffle_shop.unique_customers"
_MANIFEST = {
    "nodes": {
        _MODEL_ID: {"resource_type": "model", "config": {"materialized": "table"}},
        _TEST_ID: {"resource_type": "test", "config": {"materialized": "test"}},
    }
}
_RUN_RESULTS = {
    "metadata": {"invocation_id": "inv-1"},
    "results": [
        {
            "unique_id": _MODEL_ID,
            "status": "success",
            "execution_time": 1.5,
            "timing": [{"name": "execute", "completed_at": "2024-01-01T00:00:01Z"}],
        },
        {
            "unique_id": _TEST_ID,
            "status": "pass",
            "execution_time": 0.2,
            "timing": [{"name": "execute", "completed_at": "2024-01-01T00:00:02Z"}],
            "failures": 0,
        },
    ],
}


def test_execute_submits_async_and_sets_query_tag():
    """execute() tags the session and submits the build asynchronously, then polls."""
    component = _make_component()
    setattr(component, "get_cli_args", lambda context: ["build"])

    cursor = mock.MagicMock()
    cursor.sfqid = "build-q1"
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = (None,)  # no artifacts -> fall back, keeps test focused
    conn = _connection_returning(cursor, component)

    context = _ctx(
        log=mock.MagicMock(),
        run_id="run-xyz",
        selected_asset_keys={AssetKey(["customers"])},
        selected_asset_check_keys=set(),
    )

    with mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)):
        list(component.execute(context, _MANIFEST))

    # The build is submitted asynchronously (not via the blocking execute()).
    cursor.execute_async.assert_called_once_with(
        "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop ARGS='build'"
    )
    # The session is tagged with the Dagster run id before submitting.
    tag_calls = [c.args[0] for c in cursor.execute.call_args_list if "QUERY_TAG" in c.args[0]]
    assert len(tag_calls) == 1
    assert _QUERY_TAG_MARKER in tag_calls[0]
    assert "run-xyz" in tag_calls[0]
    # Completion is awaited and results bound.
    conn.is_still_running.assert_called()
    cursor.get_results_from_sfqid.assert_called_once_with("build-q1")


def test_execute_cancels_snowflake_query_on_interruption():
    """If the Dagster step is interrupted while polling, SYSTEM$CANCEL_QUERY is issued."""
    component = _make_component()
    setattr(component, "get_cli_args", lambda context: ["build"])

    cursor = mock.MagicMock()
    cursor.sfqid = "build-q1"
    conn = _connection_returning(cursor, component)
    # The first poll raises an interruption (run terminated).
    conn.is_still_running.side_effect = DagsterExecutionInterruptedError()
    cancel_cursor = mock.MagicMock()
    conn.cursor.side_effect = [cursor, cancel_cursor]

    context = _ctx(log=mock.MagicMock(), run_id="run-xyz")

    with (
        mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)),
        pytest.raises(DagsterExecutionInterruptedError),
    ):
        list(component.execute(context, _MANIFEST))

    cancel_cursor.execute.assert_called_once_with("SELECT SYSTEM$CANCEL_QUERY('build-q1')")


def test_execute_emits_run_results_metadata_at_parity():
    component = _make_component()
    setattr(component, "get_cli_args", lambda context: ["build"])

    cursor = mock.MagicMock()
    cursor.sfqid = "build-q1"
    cursor.fetchall.return_value = []  # dbt stdout (logged, then ignored)
    cursor.fetchone.return_value = ("snow://dbt/analytics.dbt.jaffle_shop/results/q1/",)
    _connection_returning(cursor, component)

    def fake_download(_cursor, _artifact_path, dest_dir):
        target = os.path.join(dest_dir, "results", "target")
        os.makedirs(target)
        with open(os.path.join(target, "run_results.json"), "w", encoding="utf-8") as f:
            json.dump(_RUN_RESULTS, f)

    model_key = AssetKey(["customers"])
    check_key = AssetCheckKey(asset_key=model_key, name="unique_customers")
    context = _ctx(log=mock.MagicMock(), selected_asset_check_keys={check_key})

    fake_translator = mock.MagicMock()
    fake_translator.get_asset_spec.return_value = SimpleNamespace(key=model_key)

    with (
        mock.patch.object(
            SnowflakeDbtProjectComponent, "_download_artifacts", side_effect=fake_download
        ),
        mock.patch.object(comp_mod, "validate_translator", return_value=fake_translator),
        mock.patch.object(comp_mod, "get_asset_check_key_for_test", return_value=check_key),
        mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)),
    ):
        events = list(component.execute(context, _MANIFEST))

    # The build is submitted async; the dbt log + artifacts are fetched by query id.
    cursor.execute_async.assert_called_once_with(
        "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop ARGS='build'"
    )
    issued = [c.args[0] for c in cursor.execute.call_args_list]
    assert any("SYSTEM$GET_DBT_LOG('build-q1'" in s for s in issued)
    assert any(s == "SELECT SYSTEM$LOCATE_DBT_ARTIFACTS('build-q1')" for s in issued)

    mats = [e for e in events if isinstance(e, MaterializeResult)]
    checks = [e for e in events if isinstance(e, AssetCheckResult)]

    assert len(mats) == 1
    md = mats[0].metadata
    assert mats[0].asset_key == model_key
    assert md["unique_id"] == _MODEL_ID
    assert md["invocation_id"] == "inv-1"
    assert md["execution_duration"] == 1.5
    assert "dagster_dbt/completed_at_timestamp" in md

    assert len(checks) == 1
    assert checks[0].passed is True
    assert checks[0].check_name == "unique_customers"
    assert checks[0].metadata["status"].value == "pass"


def test_execute_falls_back_when_run_results_missing():
    component = _make_component()
    setattr(component, "get_cli_args", lambda context: ["build"])

    cursor = mock.MagicMock()
    cursor.sfqid = "build-q1"
    cursor.fetchall.return_value = []  # dbt stdout
    cursor.fetchone.return_value = (None,)  # SYSTEM$LOCATE_DBT_ARTIFACTS found nothing
    _connection_returning(cursor, component)

    selected = {AssetKey(["customers"]), AssetKey(["orders"])}
    context = _ctx(
        log=mock.MagicMock(), selected_asset_keys=selected, selected_asset_check_keys=set()
    )

    with mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)):
        events = list(component.execute(context, _MANIFEST))

    assert all(isinstance(e, MaterializeResult) for e in events)
    assert {e.asset_key for e in events} == selected
    context.log.warning.assert_called_once()


# ---------------------------------------------------------------------------
# INFORMATION_SCHEMA-backed metadata
# ---------------------------------------------------------------------------

_CUST_ID = "model.jaffle_shop.customers"
_STG_ID = "model.jaffle_shop.stg_customers"
_META_MANIFEST = {
    "metadata": {"adapter_type": "snowflake"},
    "nodes": {
        _CUST_ID: {
            "resource_type": "model",
            "config": {"materialized": "table"},
            "relation_name": "DB.SCH.CUSTOMERS",
            "unique_id": _CUST_ID,
            "package_name": "jaffle_shop",
            "original_file_path": "models/customers.sql",
            "depends_on": {"nodes": [_STG_ID]},
        },
        _STG_ID: {
            "resource_type": "model",
            "config": {"materialized": "view"},
            "relation_name": "DB.SCH.STG_CUSTOMERS",
            "unique_id": _STG_ID,
            "package_name": "jaffle_shop",
            "original_file_path": "models/stg_customers.sql",
            "depends_on": {"nodes": []},
        },
    },
    "sources": {},
    "parent_map": {_CUST_ID: [_STG_ID], _STG_ID: []},
}
_META_RUN_RESULTS = {
    "metadata": {"invocation_id": "inv-1"},
    "results": [
        {
            "unique_id": _CUST_ID,
            "status": "success",
            "execution_time": 1.0,
            "timing": [{"name": "execute", "completed_at": "2024-01-01T00:00:01Z"}],
        },
        {
            "unique_id": _STG_ID,
            "status": "success",
            "execution_time": 0.5,
            "timing": [{"name": "execute", "completed_at": "2024-01-01T00:00:00Z"}],
        },
    ],
}


class _FakeCursor:
    """A cursor that routes the async-exec, LOCATE, and INFORMATION_SCHEMA queries for tests."""

    def __init__(self, located_path, info_schema_tables=None, info_schema_columns=None):
        self.sfqid = "build-q1"
        self._located = located_path
        self._tables = info_schema_tables or []  # rows of (schema, name, row_count)
        self._columns = info_schema_columns or []  # rows of (schema, name, column, data_type)
        self._last = ""
        self.executed: list[str] = []

    def execute(self, sql):
        self.executed.append(sql)
        self._last = sql

    def execute_async(self, sql):
        self.executed.append(sql)
        self._last = sql

    def get_results_from_sfqid(self, _query_id):
        pass

    def fetchone(self):
        if "SYSTEM$LOCATE_DBT_ARTIFACTS" in self._last:
            return (self._located,)
        return None

    def fetchall(self):
        if "INFORMATION_SCHEMA.TABLES" in self._last:
            return self._tables
        if "INFORMATION_SCHEMA.COLUMNS" in self._last:
            return self._columns
        return []


def _spec_for(manifest, unique_id, project):
    return SimpleNamespace(key=AssetKey([unique_id.split(".")[-1]]))


def _asset_key_for(dbt_resource_props):
    # Used by dagster-dbt's column-lineage builder to resolve parent asset keys.
    return AssetKey([dbt_resource_props["unique_id"].split(".")[-1]])


def _lineage_translator():
    translator = mock.MagicMock()
    translator.get_asset_spec.side_effect = _spec_for
    translator.get_asset_key.side_effect = _asset_key_for
    return translator


def _write_artifacts(dest_dir, *, compiled=None):
    """Create a run artifacts tree containing run_results.json and optional compiled SQL."""
    target = os.path.join(dest_dir, "results", "target")
    os.makedirs(target)
    with open(os.path.join(target, "run_results.json"), "w", encoding="utf-8") as f:
        json.dump(_META_RUN_RESULTS, f)
    for rel_path, sql in (compiled or {}).items():
        path = os.path.join(target, "compiled", "jaffle_shop", rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(sql)


def test_execute_fetches_row_counts_from_information_schema():
    component = _make_component(include_metadata=["row_count"])
    setattr(component, "get_cli_args", lambda context: ["build"])

    # INFORMATION_SCHEMA.TABLES: customers is a table (counted); stg_customers is a view
    # (NULL row_count -> skipped, like dbt core).
    cursor = _FakeCursor(
        located_path="snow://dbt/x/results/q1/",
        info_schema_tables=[("SCH", "CUSTOMERS", 42), ("SCH", "STG_CUSTOMERS", None)],
    )
    _connection_returning(cursor, component)

    context = _ctx(log=mock.MagicMock(), selected_asset_check_keys=set())
    fake_translator = _lineage_translator()

    with (
        mock.patch.object(
            SnowflakeDbtProjectComponent,
            "_download_artifacts",
            side_effect=lambda _c, _p, dest: _write_artifacts(dest),
        ),
        mock.patch.object(comp_mod, "validate_translator", return_value=fake_translator),
        mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)),
    ):
        events = list(component.execute(context, _META_MANIFEST))

    # Row counts came from a single bulk INFORMATION_SCHEMA.TABLES query, not per-model count(*).
    assert any("INFORMATION_SCHEMA.TABLES" in s for s in cursor.executed)
    assert not any(s.startswith("SELECT count(*)") for s in cursor.executed)

    by_key = {e.asset_key: e for e in events if isinstance(e, MaterializeResult)}
    row_count = by_key[AssetKey(["customers"])].metadata["dagster/row_count"]
    assert getattr(row_count, "value", row_count) == 42
    # The view was not counted.
    assert "dagster/row_count" not in by_key[AssetKey(["stg_customers"])].metadata


def test_execute_fetches_column_schema_and_lineage_from_information_schema():
    component = _make_component(include_metadata=["column_metadata"])
    setattr(component, "get_cli_args", lambda context: ["build"])

    columns = [
        ("SCH", "CUSTOMERS", "id", "NUMBER"),
        ("SCH", "CUSTOMERS", "name", "TEXT"),
        ("SCH", "STG_CUSTOMERS", "id", "NUMBER"),
        ("SCH", "STG_CUSTOMERS", "name", "TEXT"),
    ]
    cursor = _FakeCursor(located_path="snow://dbt/x/results/q1/", info_schema_columns=columns)
    _connection_returning(cursor, component)

    compiled = {
        "models/customers.sql": "SELECT id, name FROM DB.SCH.STG_CUSTOMERS",
        "models/stg_customers.sql": "SELECT 1 AS id, 2 AS name",
    }

    context = _ctx(log=mock.MagicMock(), selected_asset_check_keys=set())
    fake_translator = _lineage_translator()

    with (
        mock.patch.object(
            SnowflakeDbtProjectComponent,
            "_download_artifacts",
            side_effect=lambda _c, _p, dest: _write_artifacts(dest, compiled=compiled),
        ),
        mock.patch.object(comp_mod, "validate_translator", return_value=fake_translator),
        mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)),
    ):
        events = list(component.execute(context, _META_MANIFEST))

    # Schemas came from a bulk INFORMATION_SCHEMA.COLUMNS query, not per-model DESCRIBE TABLE.
    assert any("INFORMATION_SCHEMA.COLUMNS" in s for s in cursor.executed)
    assert not any(s.startswith("DESCRIBE TABLE") for s in cursor.executed)

    cust = next(
        e
        for e in events
        if isinstance(e, MaterializeResult) and e.asset_key == AssetKey(["customers"])
    )
    # Column schema is attached from INFORMATION_SCHEMA.COLUMNS.
    assert "dagster/column_schema" in cust.metadata
    # Column-level lineage was derived from the compiled SQL via sqlglot.
    lineage = cust.metadata["dagster/column_lineage"]
    lineage = getattr(lineage, "value", lineage)
    id_deps = lineage.deps_by_column["id"]
    assert id_deps[0].asset_key == AssetKey(["stg_customers"])
    assert id_deps[0].column_name == "id"


def test_execute_extracts_compiled_sql_from_zip_for_lineage():
    """Snowflake ships compiled SQL inside dbt_artifacts.zip; lineage works after extraction."""
    component = _make_component(include_metadata=["column_metadata"])
    setattr(component, "get_cli_args", lambda context: ["build"])

    columns = [
        ("SCH", "CUSTOMERS", "id", "NUMBER"),
        ("SCH", "CUSTOMERS", "name", "TEXT"),
        ("SCH", "STG_CUSTOMERS", "id", "NUMBER"),
        ("SCH", "STG_CUSTOMERS", "name", "TEXT"),
    ]
    cursor = _FakeCursor(located_path="snow://dbt/x/results/q1/", info_schema_columns=columns)
    _connection_returning(cursor, component)

    def fake_download(_cursor, _artifact_path, dest_dir):
        results = os.path.join(dest_dir, "results")
        os.makedirs(results)
        with open(os.path.join(results, "run_results.json"), "w", encoding="utf-8") as f:
            json.dump(_META_RUN_RESULTS, f)
        # Compiled SQL is only inside the zip, exactly like Snowflake's dbt_artifacts.zip.
        with zipfile.ZipFile(os.path.join(results, "dbt_artifacts.zip"), "w") as archive:
            archive.writestr(
                "target/compiled/jaffle_shop/models/customers.sql",
                "SELECT id, name FROM DB.SCH.STG_CUSTOMERS",
            )
            archive.writestr(
                "target/compiled/jaffle_shop/models/stg_customers.sql",
                "SELECT 1 AS id, 2 AS name",
            )

    context = _ctx(log=mock.MagicMock(), selected_asset_check_keys=set())
    fake_translator = _lineage_translator()

    with (
        mock.patch.object(
            SnowflakeDbtProjectComponent, "_download_artifacts", side_effect=fake_download
        ),
        mock.patch.object(comp_mod, "validate_translator", return_value=fake_translator),
        mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)),
    ):
        events = list(component.execute(context, _META_MANIFEST))

    cust = next(
        e
        for e in events
        if isinstance(e, MaterializeResult) and e.asset_key == AssetKey(["customers"])
    )
    lineage = cust.metadata["dagster/column_lineage"]
    lineage = getattr(lineage, "value", lineage)
    assert lineage.deps_by_column["id"][0].asset_key == AssetKey(["stg_customers"])


def test_column_metadata_merges_warehouse_types_and_dbt_descriptions():
    """The warehouse type (INFORMATION_SCHEMA) is authoritative; dbt-documented descriptions merge."""
    component = _make_component(include_metadata=["column_metadata"])

    # dbt documents the column (uppercase, with a doc-only type) + a description and tag.
    dbt_resource_props = {
        "unique_id": "model.p.customers",
        "relation_name": "DB.SCH.CUSTOMERS",
        "resource_type": "model",
        "config": {"materialized": "table"},
        "package_name": "p",
        "original_file_path": "models/customers.sql",
        "depends_on": {"nodes": []},
        "columns": {"ID": {"description": "Customer identifier", "data_type": "INTEGER"}},
    }
    manifest = {
        "metadata": {"adapter_type": "snowflake"},
        "nodes": {"model.p.customers": dbt_resource_props},
        "sources": {},
        "parent_map": {"model.p.customers": []},
    }
    fake_translator = mock.MagicMock()
    fake_translator.get_asset_spec.side_effect = _spec_for

    columns_by_relation = {"DB.SCH.CUSTOMERS": {"id": "NUMBER", "name": "TEXT"}}

    with tempfile.TemporaryDirectory() as td:  # no compiled SQL -> lineage gracefully skipped
        md = component._column_metadata(  # noqa: SLF001
            manifest, dbt_resource_props, fake_translator, Path(td), columns_by_relation
        )

    schema = md["dagster/column_schema"]
    schema = getattr(schema, "value", schema)
    cols = {c.name: c for c in schema.columns}
    assert cols["id"].type == "NUMBER"  # warehouse type wins over the dbt-documented type
    assert cols["id"].description == "Customer identifier"  # dbt doc description merged in
    assert cols["name"].type == "TEXT"  # undocumented column still present, no description
    assert cols["name"].description is None


def test_qualified_relation_fills_in_connection_defaults():
    snowflake = mock.MagicMock()
    snowflake.database = "analytics"
    snowflake.schema_ = "public"
    component = _make_component(snowflake=snowflake)
    assert component._qualified_relation('"DB"."SCH"."CUSTOMERS"') == "DB.SCH.CUSTOMERS"  # noqa: SLF001
    assert component._qualified_relation("SCH.CUSTOMERS") == "ANALYTICS.SCH.CUSTOMERS"  # noqa: SLF001
    assert component._qualified_relation("CUSTOMERS") == "ANALYTICS.PUBLIC.CUSTOMERS"  # noqa: SLF001


# ---------------------------------------------------------------------------
# Observation sensor (QUERY_TAG-based de-dup)
# ---------------------------------------------------------------------------


class _HistoryCursor:
    """A cursor that routes EXECUTION_HISTORY, QUERY_HISTORY, and LOCATE queries for sensor tests."""

    def __init__(self, history_rows, dagster_query_ids, located):
        self._history = history_rows
        self._dagster_ids = dagster_query_ids
        self._located = located
        self._last = ""

    def execute(self, sql):
        self._last = sql

    def fetchall(self):
        if "DBT_PROJECT_EXECUTION_HISTORY" in self._last:
            return self._history
        if "INFORMATION_SCHEMA.QUERY_HISTORY" in self._last:
            return [(qid,) for qid in self._dagster_ids]
        return []

    def fetchone(self):
        if "SYSTEM$LOCATE_DBT_ARTIFACTS" in self._last:
            return (self._located,)
        return None


def test_parse_project_name_fully_qualified():
    component = _make_component(snowflake_dbt_project_name="analytics.dbt.jaffle_shop")
    assert component._parse_project_name() == ("analytics", "dbt", "jaffle_shop")  # noqa: SLF001


def test_poll_external_runs_reports_new_runs_then_advances_cursor():
    component = _make_component(snowflake_dbt_project_name="analytics.dbt.jaffle_shop")
    end_time = datetime.datetime(2024, 1, 1, 0, 0, 5, tzinfo=datetime.timezone.utc)
    # (query_id, query_end_time) -- no Dagster QUERY_TAG => external run.
    cursor = _HistoryCursor(
        history_rows=[("q1", end_time)], dagster_query_ids=[], located="snow://dbt/x/results/q1/"
    )
    _connection_returning(cursor, component)

    fake_translator = mock.MagicMock()
    fake_translator.get_asset_spec.side_effect = _spec_for

    patches = (
        mock.patch.object(
            SnowflakeDbtProjectComponent,
            "_download_artifacts",
            side_effect=lambda _c, _p, dest: _write_artifacts(dest),
        ),
        mock.patch.object(comp_mod, "validate_translator", return_value=fake_translator),
    )

    with patches[0], patches[1]:
        events, new_ts = component._poll_external_runs(_META_MANIFEST, None)  # noqa: SLF001

    # External runs are reported as ad-hoc AssetMaterializations (not MaterializeResult).
    assert events and all(isinstance(e, AssetMaterialization) for e in events)
    assert {e.asset_key for e in events} == {AssetKey(["customers"]), AssetKey(["stg_customers"])}
    assert new_ts == end_time.timestamp()

    # Re-polling with the high-water-mark cursor yields nothing new (no double reporting).
    with patches[0], patches[1]:
        events2, new_ts2 = component._poll_external_runs(_META_MANIFEST, new_ts)  # noqa: SLF001
    assert events2 == []
    assert new_ts2 == new_ts


def test_poll_external_runs_skips_dagster_triggered_runs_via_query_tag():
    """Runs Dagster launched (identified by their session QUERY_TAG) are filtered out."""
    component = _make_component(snowflake_dbt_project_name="analytics.dbt.jaffle_shop")
    end_time = datetime.datetime(2024, 1, 1, 0, 0, 5, tzinfo=datetime.timezone.utc)
    # q1 appears in the QUERY_HISTORY lookup as a Dagster-tagged run, so it is skipped.
    cursor = _HistoryCursor(
        history_rows=[("q1", end_time)],
        dagster_query_ids=["q1"],
        located="snow://dbt/x/results/q1/",
    )
    _connection_returning(cursor, component)

    fake_translator = mock.MagicMock()
    fake_translator.get_asset_spec.side_effect = _spec_for

    with (
        mock.patch.object(
            SnowflakeDbtProjectComponent,
            "_download_artifacts",
            side_effect=lambda _c, _p, dest: _write_artifacts(dest),
        ),
        mock.patch.object(comp_mod, "validate_translator", return_value=fake_translator),
    ):
        events, _new_ts = component._poll_external_runs(_META_MANIFEST, None)  # noqa: SLF001

    assert events == []


def test_create_sensor_builds_sensor():
    component = _make_component(create_sensor=True)
    sensor_def = component._build_observation_sensor(_META_MANIFEST)  # noqa: SLF001
    assert sensor_def.name == "jaffle_shop__observe_dbt_runs"


def test_component_is_exported_when_dbt_installed():
    import dagster_snowflake

    assert hasattr(dagster_snowflake, "SnowflakeDbtProjectComponent")
