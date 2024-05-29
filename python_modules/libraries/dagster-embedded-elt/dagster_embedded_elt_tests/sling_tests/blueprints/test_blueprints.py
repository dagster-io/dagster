import os
import sqlite3
from pathlib import Path
from typing import Union

from dagster._core.blueprints.load_from_yaml import load_defs_from_yaml
from dagster._core.definitions.materialize import materialize
from dagster._core.test_utils import environ
from dagster_embedded_elt.sling import (
    SlingReplicationParam,
)
from dagster_embedded_elt.sling.blueprints import SlingResourceBlueprint, SlingSyncAssetsBlueprint


def test_load_basic_resources_and_sync(
    csv_to_sqlite_replication_config: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
    sqlite_connection: sqlite3.Connection,
):
    with environ(
        {
            "PATH_TO_SQLITE_DB": path_to_temp_sqlite_db,
            "PATH_TO_CSV_FILE": os.fspath(Path(__file__).parent / "test.csv"),
        }
    ):
        defs = load_defs_from_yaml(
            path=Path(__file__).parent,
            per_file_blueprint_type=Union[SlingSyncAssetsBlueprint, SlingResourceBlueprint],
        )

        res = materialize(list(defs.assets), resources=defs.resources)  # type: ignore

        assert res.success
        assert len(res.get_asset_materialization_events()) == 1

        counts = sqlite_connection.execute("SELECT count(1) FROM main.tbl").fetchone()[0]
        assert counts == 3
