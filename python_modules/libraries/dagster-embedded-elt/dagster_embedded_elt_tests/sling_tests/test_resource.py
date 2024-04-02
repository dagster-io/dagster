import json
import os
import sqlite3
import tempfile

from dagster import EnvVar, asset, file_relative_path, materialize
from dagster._core.test_utils import environ
from dagster_embedded_elt.sling import SlingMode, SlingResource
from dagster_embedded_elt.sling.resources import (
    SlingConnectionResource,
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


def test_env_var_for_permissive_field():
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
        with environ({"SQLLITE_PATH": sqllitepath}):
            target = SlingTargetConnection(type="sqlite", instance=EnvVar("SQLLITE_PATH"))

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


def test_sling_resource_env_with_source_target():
    source = SlingSourceConnection(type="duckdb", connection_string="duckdb://localhost:5000")
    target = SlingTargetConnection(type="postgres", host="abchost.com", port="420")

    sling_resource = SlingResource(source_connection=source, target_connection=target)

    env = sling_resource.prepare_environment()
    assert json.loads(env["SLING_SOURCE"]) == {"type": "duckdb", "url": "duckdb://localhost:5000"}
    assert json.loads(env["SLING_TARGET"]) == {
        "type": "postgres",
        "host": "abchost.com",
        "port": "420",
    }


def test_sling_resource_env_with_connection_resources():
    connections = [
        SlingConnectionResource(
            name="CLOUD_PRODUCTION",
            type="postgres",
            host="CLOUD_PROD_READ_REPLICA_POSTGRES_HOST",
            user="CLOUD_PROD_POSTGRES_USER",
            database="dagster",
        ),
        SlingConnectionResource(
            name="SLING_DB",
            type="snowflake",
            host="SNOWFLAKE_ACCOUNT",
            user="SNOWFLAKE_SLING_USER",
            password=EnvVar("SNOWFLAKE_SLING_PASSWORD"),
            database="sling",
        ),
    ]

    sling_resource = SlingResource(connections=connections)
    env = sling_resource.prepare_environment()

    assert json.loads(env["CLOUD_PRODUCTION"]) == {
        "name": "CLOUD_PRODUCTION",
        "type": "postgres",
        "host": "CLOUD_PROD_READ_REPLICA_POSTGRES_HOST",
        "user": "CLOUD_PROD_POSTGRES_USER",
        "database": "dagster",
    }

    assert json.loads(env["SLING_DB"]) == {
        "name": "SLING_DB",
        "type": "snowflake",
        "host": "SNOWFLAKE_ACCOUNT",
        "user": "SNOWFLAKE_SLING_USER",
        "password": EnvVar("SNOWFLAKE_SLING_PASSWORD"),
        "database": "sling",
    }


def test_sling_resource_prepares_environment_variables():
    sling_resource = SlingResource(connections=[])

    env = sling_resource.prepare_environment()
    assert "SLING_SOURCE" not in env
    assert "SLING_TARGET" not in env
