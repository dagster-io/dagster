import io
import os
import sqlite3
import tempfile

import pytest
from dagster import AssetSpec, Definitions, file_relative_path
from dagster._core.definitions.materialize import materialize
from dagster_embedded_elt.sling import (
    SlingMode,
    SlingResource,
    build_assets_from_sling_stream,
    build_sling_asset,
)
from dagster_embedded_elt.sling.resources import (
    SlingConnectionResource,
    SlingSourceConnection,
    SlingTargetConnection,
)


@pytest.fixture
def test_csv():
    return os.path.abspath(file_relative_path(__file__, "test.csv"))


@pytest.fixture
def test_staging_csv():
    return os.path.abspath(file_relative_path(__file__, "staging_test.csv"))


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        dbpath = os.path.join(tmpdir_path, "sqlite.db")
        yield dbpath


@pytest.fixture
def sling_sqlite_resource(temp_db):
    return SlingResource(
        source_connection=SlingSourceConnection(type="file"),
        target_connection=SlingTargetConnection(
            type="sqlite", connection_string=f"sqlite://{temp_db}"
        ),
    )


@pytest.fixture
def sling_file_connection():
    return SlingConnectionResource(type="file")


@pytest.fixture
def sling_staging_file_connection():
    return SlingConnectionResource(type="file")


@pytest.fixture
def sling_sqlite_connection(temp_db):
    return SlingConnectionResource(type="sqlite", connection_string=f"sqlite://{temp_db}")


@pytest.fixture
def sqlite_connection(temp_db):
    yield sqlite3.connect(temp_db)


ASSET_SPEC = AssetSpec(
    key=["main", "tbl"],
    group_name="etl",
    description="ETL Test",
    deps=["foo"],
)


@pytest.mark.parametrize(
    "mode,runs,expected", [(SlingMode.INCREMENTAL, 1, 3), (SlingMode.SNAPSHOT, 2, 6)]
)
def test_build_sling_asset(
    test_csv: str,
    sling_sqlite_resource: SlingResource,
    mode: SlingMode,
    runs: int,
    expected: int,
    sqlite_connection: sqlite3.Connection,
):
    asset_def = build_sling_asset(
        asset_spec=ASSET_SPEC,
        source_stream=f"file://{test_csv}",
        target_object="main.tbl",
        mode=mode,
        primary_key="SPECIES_CODE",
        sling_resource_key="sling_resource",
    )

    counts = None
    for _ in range(runs):
        res = materialize(
            [asset_def],
            resources={"sling_resource": sling_sqlite_resource},
        )
        assert res.success
        counts = sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0]
    assert counts == expected


def test_can_build_two_assets(
    test_csv,
    sling_sqlite_resource: SlingResource,
):
    asset_def = build_sling_asset(
        asset_spec=AssetSpec(key="asset1"),
        source_stream=f"file://{test_csv}",
        target_object="main.first_tbl",
        mode=SlingMode.FULL_REFRESH,
        primary_key="SPECIES_CODE",
        sling_resource_key="sling_resource",
    )

    asset_def_two = build_sling_asset(
        asset_spec=AssetSpec(key="asset2"),
        source_stream=f"file://{test_csv}",
        target_object="main.second_tbl",
        mode=SlingMode.FULL_REFRESH,
        primary_key="SPECIES_CODE",
        sling_resource_key="sling_resource",
    )

    defs = Definitions(
        assets=[asset_def, asset_def_two],
        resources={"sling_resource": sling_sqlite_resource},
    )

    assert defs.get_assets_def("asset1")
    assert defs.get_assets_def("asset2")


def test_update_mode(
    test_csv: str,
    sling_sqlite_resource: SlingResource,
    sqlite_connection: sqlite3.Connection,
):
    """Creates a Sling sync using Full Refresh, manually increments the UPDATE KEY to be a higher value,
    which should cause the next run not to append new rows.
    """
    asset_def_base = build_sling_asset(
        asset_spec=ASSET_SPEC,
        source_stream=f"file://{test_csv}",
        target_object="main.tbl",
        mode=SlingMode.FULL_REFRESH,
        sling_resource_key="sling_resource",
    )

    asset_def_update = build_sling_asset(
        asset_spec=ASSET_SPEC,
        source_stream=f"file://{test_csv}",
        target_object="main.tbl",
        mode=SlingMode.INCREMENTAL,
        primary_key="SPECIES_NAME",
        update_key="UPDATED_AT",
        sling_resource_key="sling_resource",
    )

    # First run should have 3 new rows
    res = materialize(
        [asset_def_base],
        resources={"sling_resource": sling_sqlite_resource},
    )
    assert res.success
    assert sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0] == 3

    # Next, manually set the UPDATED_AT to a higher value, this should prevent an append job from adding new rows.
    cur = sqlite_connection.cursor()
    cur.execute("UPDATE main.tbl set UPDATED_AT=999")
    sqlite_connection.commit()

    res = materialize(
        [asset_def_update],
        resources={"sling_resource": sling_sqlite_resource},
    )
    assert res.success
    assert sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0] == 3


@pytest.mark.parametrize(
    "text, encoding, expected",
    [
        (io.BytesIO(b"\xc6some\ndata"), "utf-8", ["\ufffdsome\n", "data"]),
        (io.BytesIO(b"\xc6some\ndata"), "latin-1", ["Æsome\n", "data"]),
    ],
)
def test_non_unicode_stdout(text, encoding, expected, sling_sqlite_resource: SlingResource):
    lines = sling_sqlite_resource.process_stdout(text, encoding)
    assert list(lines) == expected


@pytest.mark.parametrize(
    "mode,runs,expected", [(SlingMode.INCREMENTAL, 1, 3), (SlingMode.SNAPSHOT, 2, 6)]
)
def test_build_assets_from_sling_stream(
    test_csv: str,
    sling_file_connection: SlingConnectionResource,
    sling_sqlite_connection: SlingConnectionResource,
    mode: SlingMode,
    runs: int,
    expected: int,
    sqlite_connection: sqlite3.Connection,
):
    asset_def = build_assets_from_sling_stream(
        sling_file_connection,
        sling_sqlite_connection,
        stream=f"file://{test_csv}",
        target_object="main.tbl",
        mode=mode,
        primary_key="SPECIES_CODE",
    )

    counts = None
    for _ in range(runs):
        res = materialize(
            [asset_def],
            resources={
                "sling_file_connection": sling_file_connection,
                "sling_sqlite_connection": sling_sqlite_connection,
            },
        )
        assert res.success
        counts = sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0]
    assert counts == expected


def test_reuse_sling_connection_resource(
    test_csv: str,
    test_staging_csv: str,
    sling_file_connection: SlingConnectionResource,
    sling_staging_file_connection: SlingConnectionResource,
    sling_sqlite_connection: SlingConnectionResource,
    sqlite_connection: sqlite3.Connection,
):
    """Create two assets that target the same SlingConnectionResource."""
    asset_def = build_assets_from_sling_stream(
        sling_file_connection,
        sling_sqlite_connection,
        stream=f"file://{test_csv}",
        target_object="main.tbl",
        mode=SlingMode.FULL_REFRESH,
        primary_key="SPECIES_CODE",
    )

    asset_def_two = build_assets_from_sling_stream(
        sling_staging_file_connection,
        sling_sqlite_connection,
        stream=f"file://{test_staging_csv}",
        target_object="main.staging_tbl",
        mode=SlingMode.FULL_REFRESH,
        primary_key="SPECIES_CODE",
    )

    res = materialize(
        [asset_def, asset_def_two],
        resources={
            "sling_file_connection": sling_file_connection,
            "sling_staging_file_connection": sling_staging_file_connection,
            "sling_sqlite_connection": sling_sqlite_connection,
        },
    )

    assert res.success
    assert sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0] == 3
    assert sqlite_connection.execute("SELECT count(1) FROM main.staging_tbl").fetchone()[0] == 4


def test_update_mode_from_stream(
    test_csv: str,
    sling_file_connection: SlingConnectionResource,
    sling_sqlite_connection: SlingConnectionResource,
    sqlite_connection: sqlite3.Connection,
):
    """Creates a Sling sync using Full Refresh, manually increments the UPDATE KEY to be a higher value,
    which should cause the next run not to append new rows.
    """
    asset_def_base = build_assets_from_sling_stream(
        sling_file_connection,
        sling_sqlite_connection,
        stream=f"file://{test_csv}",
        target_object="main.tbl",
        mode=SlingMode.FULL_REFRESH,
    )

    asset_def_update = build_assets_from_sling_stream(
        sling_file_connection,
        sling_sqlite_connection,
        stream=f"file://{test_csv}",
        target_object="main.tbl",
        mode=SlingMode.INCREMENTAL,
        primary_key="SPECIES_NAME",
        update_key="UPDATED_AT",
    )

    res = materialize(
        [asset_def_base],
        resources={
            "sling_file_connection": sling_file_connection,
            "sling_sqlite_connection": sling_sqlite_connection,
        },
    )

    # First run should have 3 new rows
    assert res.success
    assert sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0] == 3

    # Next, manually set the UPDATED_AT to a higher value, this should prevent an append job from adding new rows.
    cur = sqlite_connection.cursor()
    cur.execute("UPDATE main.tbl set UPDATED_AT=999")
    sqlite_connection.commit()

    res = materialize(
        [asset_def_update],
        resources={
            "sling_file_connection": sling_file_connection,
            "sling_sqlite_connection": sling_sqlite_connection,
        },
    )
    assert res.success
    assert sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0] == 3
