import os
import sqlite3
from pathlib import Path

import pytest
import yaml
from dagster import AssetKey
from dagster._core.definitions import build_assets_job
from dagster_embedded_elt.sling import DagsterSlingTranslator
from dagster_embedded_elt.sling.asset_decorator import sling_assets
from dagster_embedded_elt.sling.resources import SlingMode, SlingResource
from dagster_embedded_elt.sling.sling_replication import SlingReplicationParam

replication_path = Path(__file__).joinpath("..", "sling_replication.yaml").resolve()
with replication_path.open("r") as f:
    replication = yaml.safe_load(f)


@pytest.mark.parametrize(
    "replication", [replication, replication_path, os.fspath(replication_path)]
)
def test_replication_argument(replication: SlingReplicationParam):
    @sling_assets(replication_config=replication)
    def my_sling_assets():
        ...

    assert my_sling_assets.keys == {
        AssetKey.from_user_string(key)
        for key in [
            "target/public/accounts",
            "target/public/foo_users",
            "target/public/Transactions",
            "target/public/all_users",
            "target/public/finance_departments_old",
        ]
    }


@pytest.mark.parametrize(
    "mode,runs,expected", [(SlingMode.INCREMENTAL, 1, 3), (SlingMode.SNAPSHOT, 2, 6)]
)
def test_csv_sqlite_replication(
    test_csv: str,
    sqlite_connection: sqlite3.Connection,
    sling_csv_sqlite_resource: SlingResource,
    mode: SlingMode,
    runs: int,
    expected: int,
):
    replication_config = {
        "source": "SLING_FILE",
        "target": "SLING_SQLITE",
        "defaults": {
            "mode": mode,
            "object": "{stream_schema}_{stream_name}",
        },
        "streams": {
            f"file://{test_csv}": {
                "object": "main.tbl",
                "primary_key": "SPECIES_CODE",
            }
        },
    }

    @sling_assets(replication_config=replication_config)
    def my_sling_assets(context, sling: SlingResource):
        for row in sling.replicate(
            replication_config=replication_config,
            dagster_sling_translator=DagsterSlingTranslator(),
            debug=True,
        ):
            context.log.info(row)

    sling_job = build_assets_job(
        "sling_job",
        [my_sling_assets],
        resource_defs={"sling": sling_csv_sqlite_resource},
    )

    counts = None
    for _ in range(runs):
        res = sling_job.execute_in_process()
        assert res.success
        counts = sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0]
    assert counts == expected
