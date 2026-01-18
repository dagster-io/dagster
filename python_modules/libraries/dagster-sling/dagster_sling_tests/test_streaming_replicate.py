import os
import sqlite3

from dagster import AssetExecutionContext, AssetKey, file_relative_path
from dagster._core.definitions.materialize import materialize
from dagster_sling import SlingReplicationParam, sling_assets


def test_default_sling_replicate(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
    sqlite_connection: sqlite3.Connection,
):
    from dagster_sling.resources import SlingConnectionResource, SlingResource

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
    )

    assert res.success
    asset_materializations = res.get_asset_materialization_events()
    assert len(asset_materializations) == 3

    counts = sqlite_connection.execute("SELECT count(1) FROM main.orders").fetchone()[0]
    assert counts == 4
    counts = sqlite_connection.execute("SELECT count(1) FROM main.employees").fetchone()[0]
    assert counts == 4
    counts = sqlite_connection.execute("SELECT count(1) FROM main.products").fetchone()[0]
    assert counts == 4


def test_streams_sling_replicate(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
    sqlite_connection: sqlite3.Connection,
):
    from dagster_sling.resources import SlingConnectionResource, SlingResource

    @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
    def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
        yield from sling.replicate(context=context, stream=True)

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

    counts = sqlite_connection.execute("SELECT count(1) FROM main.orders").fetchone()[0]
    assert counts == 4
    counts = sqlite_connection.execute("SELECT count(1) FROM main.employees").fetchone()[0]
    assert counts == 4
    counts = sqlite_connection.execute("SELECT count(1) FROM main.products").fetchone()[0]
    assert counts == 4


def test_stream_sling_replicate_metadata(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
    sqlite_connection: sqlite3.Connection,
):
    from dagster_sling.resources import SlingConnectionResource, SlingResource

    @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
    def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
        yield from sling.replicate(context=context, stream=True)

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
    )

    assert res.success
    asset_materializations = res.get_asset_materialization_events()
    assert len(asset_materializations) == 3

    metadatas = [
        asset_materialization.step_materialization_data.materialization.metadata
        for asset_materialization in asset_materializations
    ]

    assert all(["stream_name" in metadata for metadata in metadatas]), str(metadatas)
    assert all(["elapsed_time" in metadata for metadata in metadatas]), str(metadatas)
    assert all(["row_count" in metadata for metadata in metadatas]), str(metadatas)
    assert all(["destination_table" in metadata for metadata in metadatas]), str(metadatas)

    products_key = AssetKey(["target", "main", "products"])
    products_metadata = next(
        mat for mat in asset_materializations if mat.asset_key and mat.asset_key == products_key
    ).step_materialization_data.materialization.metadata

    path_name = os.path.abspath(
        file_relative_path(__file__, "replication_configs/csv_to_sqlite_config/dataworks/")
    )
    product_name_path = os.path.join(path_name, "Products.csv")

    assert products_metadata["stream_name"].value == f"file://{product_name_path}"
    assert products_metadata["row_count"].value == "4"
    assert products_metadata["destination_table"].value == "main.products"
