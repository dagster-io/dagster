import os
import sqlite3
from pathlib import Path

import pytest
import yaml
from dagster import (
    AssetExecutionContext,
    AssetKey,
    Config,
    FreshnessPolicy,
    JsonMetadataValue,
    file_relative_path,
)
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import TextMetadataValue
from dagster._core.definitions.tags import build_kind_tag
from dagster_embedded_elt.sling import SlingReplicationParam, sling_assets
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
    path_to_temp_sqlite_db: str,
    sqlite_connection: sqlite3.Connection,
):
    @sling_assets(replication_config=csv_to_sqlite_replication_config)
    def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
        yield from sling.replicate(context=context)

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
    assert len(res.get_asset_materialization_events()) == 1

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
    replication_config_path = file_relative_path(
        __file__, "replication_configs/base_with_meta_config/replication.yaml"
    )
    replication_config = yaml.safe_load(Path(replication_config_path).read_bytes())

    @sling_assets(replication_config=replication_config_path)
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
        AssetKey(["target", "public", "accounts"]): {
            "stream_config": JsonMetadataValue(data=None),
            "dagster_embedded_elt/dagster_sling_translator": DagsterSlingTranslator(
                target_prefix="target"
            ),
            "dagster_embedded_elt/sling_replication_config": replication_config,
        },
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
            ),
            "dagster_embedded_elt/dagster_sling_translator": DagsterSlingTranslator(
                target_prefix="target"
            ),
            "dagster_embedded_elt/sling_replication_config": replication_config,
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
            ),
            "dagster_embedded_elt/dagster_sling_translator": DagsterSlingTranslator(
                target_prefix="target"
            ),
            "dagster_embedded_elt/sling_replication_config": replication_config,
        },
        AssetKey(["target", "public", "all_users"]): {
            "stream_config": JsonMetadataValue(
                data={
                    "sql": 'select all_user_id, name \nfrom public."all_Users"\n',
                    "object": "public.all_users",
                }
            ),
            "dagster_embedded_elt/dagster_sling_translator": DagsterSlingTranslator(
                target_prefix="target"
            ),
            "dagster_embedded_elt/sling_replication_config": replication_config,
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


def test_base_with_custom_tags_translator() -> None:
    replication_config_path = file_relative_path(
        __file__, "replication_configs/base_with_default_meta/replication.yaml"
    )

    class CustomSlingTranslator(DagsterSlingTranslator):
        def get_tags(self, stream_definition):
            return {"custom_tag": "custom_value"}

    @sling_assets(
        replication_config=replication_config_path,
        dagster_sling_translator=CustomSlingTranslator(),
    )
    def my_sling_assets(): ...

    for asset_key in my_sling_assets.keys:
        assert my_sling_assets.tags_by_key[asset_key] == {
            "custom_tag": "custom_value",
            **build_kind_tag("sling"),
        }


def test_base_with_default_meta_translator():
    replication_config_path = file_relative_path(
        __file__, "replication_configs/base_with_default_meta/replication.yaml"
    )
    replication_config = yaml.safe_load(Path(replication_config_path).read_bytes())

    @sling_assets(replication_config=replication_config_path)
    def my_sling_assets(): ...

    assert my_sling_assets.metadata_by_key == {
        AssetKey(["target", "public", "accounts"]): {
            "stream_config": JsonMetadataValue(data={"meta": {"dagster": {"group": "group_1"}}}),
            "dagster_embedded_elt/dagster_sling_translator": DagsterSlingTranslator(
                target_prefix="target"
            ),
            "dagster_embedded_elt/sling_replication_config": replication_config,
        },
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
            ),
            "dagster_embedded_elt/dagster_sling_translator": DagsterSlingTranslator(
                target_prefix="target"
            ),
            "dagster_embedded_elt/sling_replication_config": replication_config,
        },
        AssetKey(["target", "public", "transactions"]): {
            "stream_config": JsonMetadataValue(
                data={
                    "mode": "incremental",
                    "primary_key": "id",
                    "update_key": "last_updated_at",
                    "meta": {
                        "dagster": {
                            "group": "group_1",
                            "description": "Example Description!",
                            "auto_materialize_policy": True,
                        }
                    },
                }
            ),
            "dagster_embedded_elt/dagster_sling_translator": DagsterSlingTranslator(
                target_prefix="target"
            ),
            "dagster_embedded_elt/sling_replication_config": replication_config,
        },
        AssetKey(["target", "public", "all_users"]): {
            "stream_config": JsonMetadataValue(
                data={
                    "sql": 'select all_user_id, name\nfrom public."all_Users"\n',
                    "object": "public.all_users",
                    "meta": {"dagster": {"group": "group_1"}},
                }
            ),
            "dagster_embedded_elt/dagster_sling_translator": DagsterSlingTranslator(
                target_prefix="target"
            ),
            "dagster_embedded_elt/sling_replication_config": replication_config,
        },
    }

    assert my_sling_assets.group_names_by_key == {
        AssetKey(["target", "public", "all_users"]): "group_1",
        AssetKey(["target", "public", "accounts"]): "group_1",
        AssetKey(["target", "public", "transactions"]): "group_1",
        AssetKey(["target", "departments"]): "group_2",
    }


def test_base_with_custom_asset_key_prefix():
    @sling_assets(
        replication_config=file_relative_path(
            __file__, "replication_configs/base_config/replication.yaml"
        ),
        dagster_sling_translator=DagsterSlingTranslator(target_prefix="custom"),
    )
    def my_sling_assets(): ...

    assert my_sling_assets.keys == {
        AssetKey(["custom", "public", "users"]),
        AssetKey(["custom", "public", "accounts"]),
        AssetKey(["custom", "public", "all_users"]),
        AssetKey(["custom", "departments"]),
        AssetKey(["custom", "public", "transactions"]),
    }


def test_subset_with_asset_selection(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
):
    @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
    def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
        yield from sling.replicate(context=context)

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
    res = materialize(
        [my_sling_assets],
        resources={"sling": sling_resource},
        selection=[AssetKey(["target", "main", "orders"])],
    )

    assert res.success
    asset_materializations = res.get_asset_materialization_events()
    assert len(asset_materializations) == 1
    found_asset_keys = {
        mat.event_specific_data.materialization.asset_key  # pyright: ignore
        for mat in asset_materializations
    }
    assert found_asset_keys == {AssetKey(["target", "main", "orders"])}

    res = materialize(
        [my_sling_assets],
        resources={"sling": sling_resource},
        selection=[
            AssetKey(["target", "main", "employees"]),
            AssetKey(["target", "main", "products"]),
        ],
    )

    assert res.success
    asset_materializations = res.get_asset_materialization_events()
    assert len(asset_materializations) == 2
    found_asset_keys = {
        mat.event_specific_data.materialization.asset_key  # pyright: ignore
        for mat in asset_materializations
    }
    assert found_asset_keys == {
        AssetKey(["target", "main", "employees"]),
        AssetKey(["target", "main", "products"]),
    }


def test_subset_with_run_config(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
    path_to_dataworks_folder: str,
):
    class MyAssetConfig(Config):
        context_streams: dict = {}

    @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
    def my_sling_assets(
        context: AssetExecutionContext, sling: SlingResource, config: MyAssetConfig
    ):
        yield from sling.replicate(context=context)

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
    res = materialize(
        [my_sling_assets],
        resources={"sling": sling_resource},
        run_config={},
    )

    assert res.success
    asset_materializations = res.get_asset_materialization_events()
    assert len(asset_materializations) == 3  # no 'context_streams', no subset performed
    found_asset_keys = {
        mat.event_specific_data.materialization.asset_key  # pyright: ignore
        for mat in asset_materializations
    }
    assert found_asset_keys == {
        AssetKey(["target", "main", "employees"]),
        AssetKey(["target", "main", "orders"]),
        AssetKey(["target", "main", "products"]),
    }

    res = materialize(
        [my_sling_assets],
        resources={"sling": sling_resource},
        run_config={
            "ops": {
                "my_sling_assets": {
                    "config": {
                        "context_streams": {
                            f'file://{os.path.join(path_to_dataworks_folder, "Orders.csv")}': {
                                "object": "main.orders"
                            }
                        }
                    }
                }
            }
        },
    )

    assert res.success
    asset_materializations = res.get_asset_materialization_events()
    assert len(asset_materializations) == 1
    found_asset_keys = {
        mat.event_specific_data.materialization.asset_key  # pyright: ignore
        for mat in asset_materializations
    }
    assert found_asset_keys == {
        AssetKey(["target", "main", "orders"]),
    }


def test_relation_identifier(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
):
    @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
    def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
        yield from sling.replicate(context=context)

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
    res = materialize(
        [my_sling_assets],
        resources={"sling": sling_resource},
        selection=[AssetKey(["target", "main", "orders"])],
    )

    assert res.success
    asset_materializations = res.get_asset_materialization_events()
    assert len(asset_materializations) == 1
    assert asset_materializations[0].materialization.metadata[
        "dagster/relation_identifier"
    ] == TextMetadataValue(text="SLING_SQLITE.main.orders")
