import logging
import sqlite3

import pytest
from dagster import (
    AssetKey,
    FreshnessPolicy,
    JsonMetadataValue,
    file_relative_path,
)
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
    def my_sling_assets(): ...

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


def test_disabled_asset():
    @sling_assets(
        replication_config=file_relative_path(
            __file__, "replication_configs/base_config_disabled/replication.yaml"
        )
    )
    def my_sling_assets(): ...

    assert my_sling_assets.keys == {
        AssetKey.from_user_string(key)
        for key in [
            "target/public/accounts",
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


def test_with_custom_name(replication_config: SlingReplicationParam):
    @sling_assets(replication_config=replication_config)
    def my_sling_assets(): ...

    assert my_sling_assets.op.name == "my_sling_assets"

    @sling_assets(replication_config=replication_config)
    def my_other_assets(): ...

    assert my_other_assets.op.name == "my_other_assets"

    @sling_assets(replication_config=replication_config, name="custom_name")
    def my_third_sling_assets(): ...

    assert my_third_sling_assets.op.name == "custom_name"


def test_base_with_meta_config_translator():
    @sling_assets(
        replication_config=file_relative_path(
            __file__, "replication_configs/base_with_meta_config/replication.yaml"
        )
    )
    def my_sling_assets(): ...

    assert my_sling_assets.keys == {
        AssetKey(["target", "public", "all_users"]),
        AssetKey(["target", "public", "accounts"]),
        AssetKey(["target", "public", "transactions"]),
        AssetKey(["target", "departments"]),
    }

    assert my_sling_assets.asset_deps == {
        AssetKey(["target", "public", "accounts"]): {AssetKey(["public", "accounts"])},
        AssetKey(["target", "departments"]): {AssetKey(["foo_one"]), AssetKey(["foo_two"])},
        AssetKey(["target", "public", "transactions"]): {AssetKey(["public", "transactions"])},
        AssetKey(["target", "public", "all_users"]): {AssetKey(["public", "all_users"])},
    }

    assert my_sling_assets.descriptions_by_key == {
        AssetKey(["target", "public", "transactions"]): "Example Description!",
        AssetKey(
            ["target", "public", "all_users"]
        ): 'select all_user_id, name \nfrom public."all_Users"\n',
    }

    assert my_sling_assets.metadata_by_key == {
        AssetKey(["target", "public", "accounts"]): {"stream_config": JsonMetadataValue(data=None)},
        AssetKey(["target", "departments"]): {
            "stream_config": JsonMetadataValue(
                data={
                    "object": "departments",
                    "source_options": {"empty_as_null": False},
                    "meta": {
                        "dagster": {
                            "deps": ["foo_one", "foo_two"],
                            "group": "group_2",
                            "freshness_policy": {
                                "maximum_lag_minutes": 0,
                                "cron_schedule": "5 4 * * *",
                                "cron_schedule_timezone": "UTC",
                            },
                        }
                    },
                }
            )
        },
        AssetKey(["target", "public", "transactions"]): {
            "stream_config": JsonMetadataValue(
                data={
                    "mode": "incremental",
                    "primary_key": "id",
                    "update_key": "last_updated_at",
                    "meta": {
                        "dagster": {
                            "description": "Example Description!",
                            "auto_materialize_policy": True,
                        }
                    },
                }
            )
        },
        AssetKey(["target", "public", "all_users"]): {
            "stream_config": JsonMetadataValue(
                data={
                    "sql": 'select all_user_id, name \nfrom public."all_Users"\n',
                    "object": "public.all_users",
                }
            )
        },
    }

    assert my_sling_assets.group_names_by_key == {
        AssetKey(["target", "public", "all_users"]): "default",
        AssetKey(["target", "public", "accounts"]): "default",
        AssetKey(["target", "public", "transactions"]): "default",
        AssetKey(["target", "departments"]): "group_2",
    }

    assert my_sling_assets.freshness_policies_by_key == {
        AssetKey(["target", "departments"]): FreshnessPolicy(
            maximum_lag_minutes=0.0, cron_schedule="5 4 * * *", cron_schedule_timezone="UTC"
        )
    }

    assert (
        AssetKey(["target", "public", "transactions"])
        in my_sling_assets.auto_materialize_policies_by_key
    )
