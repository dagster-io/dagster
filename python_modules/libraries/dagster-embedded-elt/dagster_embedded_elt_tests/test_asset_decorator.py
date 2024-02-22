import logging
import sqlite3

import pytest
from dagster import AssetKey
from dagster._core.definitions.materialize import materialize
from dagster_embedded_elt.sling import (
    SlingReplicationParam,
    sling_assets,
)
from dagster_embedded_elt.sling.dagster_sling_translator import DagsterSlingTranslator
from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource


@pytest.mark.parametrize(
    "replication_params",
    ["base_replication_config", "base_replication_config_path", "os_fspath"],
    indirect=True,
)
def test_replication_param_defs(replication_params: SlingReplicationParam):
    @sling_assets(replication_config=replication_params)
    def my_sling_assets():
        ...

    assert my_sling_assets.keys == {
        AssetKey.from_user_string(key)
        for key in [
            "target/public/accounts",
            "target/public/users",
            "target/departments",
            "target/public/transactions",
            "target/public/all_users",
        ]
    }


def test_runs_base_sling_config(
    csv_to_sqlite_replication_config: SlingReplicationParam,
    path_to_test_csv: str,
    path_to_temp_sqlite_db: str,
    sqlite_connection: sqlite3.Connection,
):
    @sling_assets(replication_config=csv_to_sqlite_replication_config)
    def my_sling_assets(sling: SlingResource):
        for row in sling.replicate(
            replication_config=csv_to_sqlite_replication_config,
            dagster_sling_translator=DagsterSlingTranslator(),
        ):
            logging.info(row)

    sling_resource = SlingResource(
        connections=[
            SlingConnectionResource(type="file", name="SLING_FILE"),
            SlingConnectionResource(
                type="sqlite",
                name="SLING_SQLITE",
                connection_string=f"sqlite://{path_to_temp_sqlite_db}",
            ),
        ]
    )
    res = materialize([my_sling_assets], resources={"sling": sling_resource})
    assert res.success
    counts = sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0]
    assert counts == 3
