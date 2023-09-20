from dagster import asset, materialize, file_relative_path
from dagster_elt import SlingResource, SlingSource, SlingMode, SlingTarget
import os
import tempfile
import sqlite3


def test_resource():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        fpath = os.path.abspath(file_relative_path(__file__, "test.csv"))
        dbpath = os.path.join(tmpdir_path, "sqlite.db")
        sling_source = SlingSource(
            stream=f"file://{fpath}",
            primary_key=["SPECIES_CODE"],
        )

        sling_target = SlingTarget(object="main.tbl")

        @asset
        def run_sync(context, sling: SlingResource):
            res = sling.sync(source=sling_source, target=sling_target, mode=SlingMode.FULL_REFRESH)
            for stdout in res:
                context.log.debug(stdout)
            counts = sqlite3.connect(dbpath).execute("SELECT count(1) FROM main.tbl").fetchone()
            assert counts[0] == 3

        materialize(
            [run_sync],
            resources={
                "sling": SlingResource(
                    source_connection=None,
                    target_connection=f"sqlite://{dbpath}",
                    mode=SlingMode.TRUNCATE,
                )
            },
        )
