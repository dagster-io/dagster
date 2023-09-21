import os
import sqlite3
import tempfile

from dagster import AssetKey, file_relative_path
from dagster._core.definitions import build_assets_job
from dagster_elt import SlingMode, SlingSource, SlingTarget, SlingResource
from dagster_elt.asset_defs import build_sling_asset


def test_build_sling_asset():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        fpath = os.path.abspath(file_relative_path(__file__, "test.csv"))
        dbpath = os.path.join(tmpdir_path, "sqlite.db")

        sling_resource = SlingResource(
            source_connection=None,
            target_connection=f"sqlite://{dbpath}",
            mode=SlingMode.TRUNCATE,
        )

        asset_def = build_sling_asset(
            key=AssetKey("sling_key"),
            sling_resource_key="sling_resource",
            source_table=f"file://{fpath}",
            dest_table="main.tbl",
            mode=SlingMode.INCREMENTAL,
            primary_key="SPECIES_CODE",
            deps=["foo"],
        )

        sling_job = build_assets_job(
            "sling_job",
            [asset_def],
            resource_defs={"sling_resource": sling_resource},
        )

        res = sling_job.execute_in_process()
        assert res.success
        counts = sqlite3.connect(dbpath).execute("SELECT count(1) FROM main.tbl").fetchone()
        assert counts[0] == 3
