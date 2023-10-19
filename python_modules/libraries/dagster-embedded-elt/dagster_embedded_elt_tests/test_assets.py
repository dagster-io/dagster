import os
import sqlite3
import tempfile
from typing import Literal

import pytest
from dagster import AssetSpec, Definitions, file_relative_path
from dagster._core.definitions import build_assets_job
from dagster_embedded_elt.sling import SlingMode, SlingResource, build_sling_asset
from dagster_embedded_elt.sling.resources import SlingSourceConnection, SlingTargetConnection


@pytest.mark.parametrize(
    "mode,runs,expected", [(SlingMode.INCREMENTAL, 1, 3), (SlingMode.SNAPSHOT, 2, 6)]
)
def test_build_sling_asset(mode: SlingMode, runs: int, expected: int):
    with tempfile.TemporaryDirectory() as tmpdir_path:
        fpath = os.path.abspath(file_relative_path(__file__, "test.csv"))
        dbpath = os.path.join(tmpdir_path, "sqlite.db")

        sling_resource = SlingResource(
            source_connection=SlingSourceConnection(type="file"),
            target_connection=SlingTargetConnection(
                type="sqlite", connection_string=f"sqlite://{dbpath}"
            ),
        )

        asset_spec = AssetSpec(
            key=["main", "tbl"],
            group_name="etl",
            description="ETL Test",
            deps=["foo"],
        )
        asset_def = build_sling_asset(
            asset_spec=asset_spec,
            source_stream=f"file://{fpath}",
            target_object="main.tbl",
            mode=mode,
            primary_key="SPECIES_CODE",
            sling_resource_key="sling_resource",
        )

        sling_job = build_assets_job(
            "sling_job",
            [asset_def],
            resource_defs={"sling_resource": sling_resource},
        )

        counts = None
        for n in range(runs):
            res = sling_job.execute_in_process()
            assert res.success
            counts = sqlite3.connect(dbpath).execute("SELECT count(1) FROM main.tbl").fetchone()[0]
        assert counts == expected


def test_can_build_two_assets():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        fpath = os.path.abspath(file_relative_path(__file__, "test.csv"))
        dbpath = os.path.join(tmpdir_path, "sqlite.db")

        sling_resource = SlingResource(
            source_connection=SlingSourceConnection(type="file"),
            target_connection=SlingTargetConnection(
                type="sqlite", connection_string=f"sqlite://{dbpath}"
            ),
        )

        asset_def = build_sling_asset(
            asset_spec=AssetSpec(key="asset1"),
            source_stream=f"file://{fpath}",
            target_object="main.first_tbl",
            mode=SlingMode.FULL_REFRESH,
            primary_key="SPECIES_CODE",
            sling_resource_key="sling_resource",
        )

        asset_def_two = build_sling_asset(
            asset_spec=AssetSpec(key="asset2"),
            source_stream=f"file://{fpath}",
            target_object="main.second_tbl",
            mode=SlingMode.FULL_REFRESH,
            primary_key="SPECIES_CODE",
            sling_resource_key="sling_resource",
        )

        defs = Definitions(
            assets=[asset_def, asset_def_two],
            resources={"sling_resource": sling_resource},
        )

        assert defs.get_assets_def("asset1")
        assert defs.get_assets_def("asset2")
