import logging

from dagster import asset, materialize, file_relative_path, op, job, RunConfig
from dagster_elt import SlingResource, SlingSource, SlingMode, SlingTarget, SlingSyncConfig
from dagster_elt.ops import sling_sync_op
import os
import tempfile
import sqlite3


log = logging.getLogger(__name__)


def test_airbyte_sync_op_cloud() -> None:
    with tempfile.TemporaryDirectory() as tmpdir_path:
        fpath = os.path.abspath(file_relative_path(__file__, "test.csv"))
        dbpath = os.path.join(tmpdir_path, "sqlite.db")
        sling_source = SlingSource(
            stream=f"file://{fpath}",
            primary_key=["SPECIES_CODE"],
        )

        sling_target = SlingTarget(object="main.tbl")
        sling_resource = SlingResource(
            source_connection=None,
            target_connection=f"sqlite://{dbpath}",
            mode=SlingMode.TRUNCATE,
        )
        config = RunConfig(
            {
                "sling_sync_op": SlingSyncConfig(
                    source=sling_source, target=sling_target, mode=SlingMode.FULL_REFRESH
                )
            }
        )

        @op
        def foo_op() -> None:
            pass

        @job(resource_defs={"sling": sling_resource}, config=config)
        def sling_sync_job() -> None:
            sling_sync_op(start_after=foo_op())

        res = sling_sync_job.execute_in_process()
        log.debug(res)
        counts = sqlite3.connect(dbpath).execute("SELECT count(1) FROM main.tbl").fetchone()
        assert counts[0] == 3
