import os
import sqlite3
import tempfile

from dagster import asset, file_relative_path, materialize
from dagster_embedded_elt.sling import SlingMode, SlingResource
from dagster_embedded_elt.sling.resources import (
    SlingSourceConnection,
    SlingTargetConnection,
)


def test_simple_resource_connection():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        sqllitepath = os.path.join(tmpdir_path, "sqlite.db")

        @asset
        def run_sync(context, sling: SlingResource):
            res = sling.sync(
                source_stream=os.path.join(file_relative_path(__file__, "test.csv")),
                target_object="main.events",
                mode=SlingMode.FULL_REFRESH,
            )
            # Consume the generator by printing to stdout
            for stdout in res:
                context.log.debug(stdout)
            counts = sqlite3.connect(sqllitepath).execute("SELECT count(1) FROM events").fetchone()
            assert counts[0] == 3

        source = SlingSourceConnection(
            type="file",
        )
        target = SlingTargetConnection(type="sqlite", instance=sqllitepath)

        materialize(
            [run_sync],
            resources={
                "sling": SlingResource(
                    source_connection=source,
                    target_connection=target,
                    mode=SlingMode.TRUNCATE,
                )
            },
        )


def test_resource_connection_with_source_options():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        sqllitepath = os.path.join(tmpdir_path, "sqlite.db")

        @asset
        def run_sync(context, sling: SlingResource):
            res = sling.sync(
                source_stream=os.path.join(file_relative_path(__file__, "test_json.no_ext")),
                target_object="main.events",
                mode=SlingMode.FULL_REFRESH,
                source_options={"format": "json"},
            )
            for stdout in res:
                context.log.debug(stdout)
            counts = sqlite3.connect(sqllitepath).execute("SELECT count(1) FROM events").fetchone()
            assert counts[0] == 3

        source = SlingSourceConnection(
            type="file",
        )
        target = SlingTargetConnection(type="sqlite", instance=sqllitepath)

        materialize(
            [run_sync],
            resources={
                "sling": SlingResource(
                    source_connection=source,
                    target_connection=target,
                    mode=SlingMode.TRUNCATE,
                )
            },
        )
