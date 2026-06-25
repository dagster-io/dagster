"""Tests for SnowflakeDbtProjectComponent.

These tests focus on the logic that is unique to driving a dbt project natively on
Snowflake -- the `EXECUTE DBT PROJECT` SQL generation, fetching the manifest from
Snowflake, and translating `run_results.json` into Dagster events with metadata at parity
with dbt core / dbt Cloud -- without standing up a real dbt project or Snowflake connection.
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

# Skip the whole module if the optional `dagster-dbt` dependency is not installed.
pytest.importorskip("dagster_dbt")

import dagster_snowflake.components.dbt_project.component as comp_mod
from dagster_snowflake.components.dbt_project.component import (
    SnowflakeDbtProjectComponent,
    _default_op_name,
    build_dbt_project_execution_history_sql,
    build_execute_dbt_project_sql,
    build_get_dbt_log_sql,
    build_locate_artifacts_sql,
)


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


def test_default_op_name_sanitizes_qualified_name():
    assert _default_op_name("analytics.dbt.jaffle_shop") == "jaffle_shop"
    assert _default_op_name("my-project") == "my_project"


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
    return SimpleNamespace(**kwargs)


def _connection_returning(cursor: Any, component: SnowflakeDbtProjectComponent) -> None:
    conn = mock.MagicMock()
    conn.cursor.return_value = cursor
    cast("Any", component.snowflake).get_connection.return_value.__enter__.return_value = conn


def test_write_state_fetches_manifest_from_snowflake(tmp_path):
    component = _make_component(manifest_args=["parse"])

    cursor = mock.MagicMock()
    cursor.sfqid = "query-123"
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
    assert issued[0] == "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop ARGS='parse'"
    assert issued[1] == "SELECT SYSTEM$LOCATE_DBT_ARTIFACTS('query-123')"


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

    # The build statement runs first; the dbt log is fetched and artifacts located by query id.
    issued = [c.args[0] for c in cursor.execute.call_args_list]
    assert issued[0] == "EXECUTE DBT PROJECT analytics.dbt.jaffle_shop ARGS='build'"
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
    """A minimal cursor that routes EXECUTE/LOCATE/DESCRIBE/COUNT queries for tests."""

    def __init__(self, located_path, columns_by_relation, row_counts):
        self.sfqid = "build-q1"
        self._located = located_path
        self._columns = columns_by_relation
        self._row_counts = row_counts
        self._last = ""
        self.executed: list[str] = []

    def execute(self, sql):
        self.executed.append(sql)
        self._last = sql

    def fetchone(self):
        if "SYSTEM$LOCATE_DBT_ARTIFACTS" in self._last:
            return (self._located,)
        if self._last.startswith("SELECT count(*)"):
            return (self._row_counts[self._last.split("FROM ")[-1].strip()],)
        return None

    def fetchall(self):
        if self._last.startswith("DESCRIBE TABLE"):
            relation = self._last[len("DESCRIBE TABLE ") :].strip()
            return [(name, meta["data_type"]) for name, meta in self._columns[relation].items()]
        return []


def _spec_for(manifest, unique_id, project):
    return SimpleNamespace(key=AssetKey([unique_id.split(".")[-1]]))


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


def test_execute_fetches_row_counts():
    component = _make_component(include_metadata=["row_count"])
    setattr(component, "get_cli_args", lambda context: ["build"])

    # customers is a table (counted); stg_customers is a view (skipped, like dbt core).
    cursor = _FakeCursor(
        located_path="snow://dbt/x/results/q1/",
        columns_by_relation={},
        row_counts={"DB.SCH.CUSTOMERS": 42},
    )
    _connection_returning(cursor, component)

    context = _ctx(log=mock.MagicMock(), selected_asset_check_keys=set())
    fake_translator = mock.MagicMock()
    fake_translator.get_asset_spec.side_effect = _spec_for

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

    by_key = {e.asset_key: e for e in events if isinstance(e, MaterializeResult)}
    row_count = by_key[AssetKey(["customers"])].metadata["dagster/row_count"]
    assert getattr(row_count, "value", row_count) == 42
    # The view was not counted.
    assert "dagster/row_count" not in by_key[AssetKey(["stg_customers"])].metadata


def test_execute_fetches_column_schema_and_lineage():
    component = _make_component(include_metadata=["column_metadata"])
    setattr(component, "get_cli_args", lambda context: ["build"])

    columns = {"id": {"data_type": "NUMBER"}, "name": {"data_type": "TEXT"}}
    cursor = _FakeCursor(
        located_path="snow://dbt/x/results/q1/",
        columns_by_relation={"DB.SCH.CUSTOMERS": columns, "DB.SCH.STG_CUSTOMERS": columns},
        row_counts={},
    )
    _connection_returning(cursor, component)

    compiled = {
        "models/customers.sql": "SELECT id, name FROM DB.SCH.STG_CUSTOMERS",
        "models/stg_customers.sql": "SELECT 1 AS id, 2 AS name",
    }

    context = _ctx(log=mock.MagicMock(), selected_asset_check_keys=set())
    fake_translator = mock.MagicMock()
    fake_translator.get_asset_spec.side_effect = _spec_for

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

    cust = next(
        e
        for e in events
        if isinstance(e, MaterializeResult) and e.asset_key == AssetKey(["customers"])
    )
    # Column schema is attached from DESCRIBE TABLE.
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

    columns = {"id": {"data_type": "NUMBER"}, "name": {"data_type": "TEXT"}}
    cursor = _FakeCursor(
        located_path="snow://dbt/x/results/q1/",
        columns_by_relation={"DB.SCH.CUSTOMERS": columns, "DB.SCH.STG_CUSTOMERS": columns},
        row_counts={},
    )
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
    fake_translator = mock.MagicMock()
    fake_translator.get_asset_spec.side_effect = _spec_for

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


def test_fetch_column_metadata_merges_warehouse_types_and_dbt_descriptions():
    """The warehouse type (DESCRIBE) is authoritative; dbt-documented descriptions are merged in."""
    component = _make_component(include_metadata=["column_metadata"])
    cursor = _FakeCursor(
        located_path="snow://x/",
        columns_by_relation={
            "DB.SCH.CUSTOMERS": {"id": {"data_type": "NUMBER"}, "name": {"data_type": "TEXT"}}
        },
        row_counts={},
    )
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

    with tempfile.TemporaryDirectory() as td:  # no compiled SQL -> lineage gracefully skipped
        md = component._fetch_column_metadata(  # noqa: SLF001
            cursor, manifest, dbt_resource_props, fake_translator, Path(td), {}
        )

    schema = md["dagster/column_schema"]
    schema = getattr(schema, "value", schema)
    cols = {c.name: c for c in schema.columns}
    assert cols["id"].type == "NUMBER"  # warehouse type wins over the dbt-documented type
    assert cols["id"].description == "Customer identifier"  # dbt doc description merged in
    assert cols["name"].type == "TEXT"  # undocumented column still present, no description
    assert cols["name"].description is None


class _HistoryCursor:
    """A cursor that routes DBT_PROJECT_EXECUTION_HISTORY + LOCATE queries for sensor tests."""

    def __init__(self, rows, located):
        self._rows = rows
        self._located = located
        self._last = ""

    def execute(self, sql):
        self._last = sql

    def fetchall(self):
        if "DBT_PROJECT_EXECUTION_HISTORY" in self._last:
            return self._rows
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
    # (query_id, query_end_time, args) -- args has no Dagster marker => external run.
    cursor = _HistoryCursor(rows=[("q1", end_time, "build")], located="snow://dbt/x/results/q1/")
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


def test_poll_external_runs_skips_dagster_triggered_runs():
    """Runs Dagster launched (marked via the sentinel dbt var) are filtered out, like dbt Cloud."""
    component = _make_component(snowflake_dbt_project_name="analytics.dbt.jaffle_shop")
    end_time = datetime.datetime(2024, 1, 1, 0, 0, 5, tzinfo=datetime.timezone.utc)
    marked_args = 'build --vars {"dagster_managed_by_component":true}'
    cursor = _HistoryCursor(
        rows=[("q1", end_time, marked_args)], located="snow://dbt/x/results/q1/"
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


def test_create_sensor_marks_runs_and_builds_sensor():
    component = _make_component(create_sensor=True)
    setattr(component, "get_cli_args", lambda context: ["build"])

    # When the sensor is enabled, op-triggered runs are tagged so the sensor can skip them.
    with mock.patch.object(comp_mod, "get_subset_selection_for_context", return_value=([], None)):
        sql = component.build_execute_sql(_ctx(), {})
    assert '--vars {"dagster_managed_by_component":true}' in sql

    sensor_def = component._build_observation_sensor(_META_MANIFEST)  # noqa: SLF001
    assert sensor_def.name == "jaffle_shop__observe_dbt_runs"


def test_component_is_exported_when_dbt_installed():
    import dagster_snowflake

    assert hasattr(dagster_snowflake, "SnowflakeDbtProjectComponent")
