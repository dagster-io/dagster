import mock
from dagster import AssetExecutionContext, AssetKey
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata.metadata_value import (
    TableColumnLineageMetadataValue,
    TableSchemaMetadataValue,
)
from dagster._core.definitions.metadata.table import (
    TableColumn,
    TableColumnDep,
    TableColumnLineage,
    TableSchema,
)
from dagster_embedded_elt.sling import SlingReplicationParam, sling_assets


def test_fetch_column_metadata(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
):
    from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource

    @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
    def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
        yield from sling.replicate(context=context).fetch_column_metadata()

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
    assert all(["dagster/column_schema" in metadata for metadata in metadatas]), str(metadatas)
    assert all(["dagster/column_lineage" in metadata for metadata in metadatas]), str(metadatas)

    products_key = AssetKey(["target", "main", "products"])
    products_metadata = next(
        mat for mat in asset_materializations if mat.asset_key and mat.asset_key == products_key
    ).step_materialization_data.materialization.metadata

    assert products_metadata["dagster/column_schema"] == TableSchemaMetadataValue(
        schema=TableSchema(
            columns=[
                TableColumn(name="product_id", type="bigint"),
                TableColumn(name="name", type="text"),
                TableColumn(name="category", type="text"),
                TableColumn(name="price", type="decimal"),
                TableColumn(name="_sling_loaded_at", type="bigint"),
            ]
        )
    )

    # upstream key is gross filepath thing, we just extract it
    upstream_key = next(iter(my_sling_assets.asset_deps[products_key]))
    assert products_metadata["dagster/column_lineage"] == TableColumnLineageMetadataValue(
        column_lineage=TableColumnLineage(
            deps_by_column={
                "product_id": [TableColumnDep(asset_key=upstream_key, column_name="product_id")],
                "name": [TableColumnDep(asset_key=upstream_key, column_name="name")],
                "category": [TableColumnDep(asset_key=upstream_key, column_name="category")],
                "price": [TableColumnDep(asset_key=upstream_key, column_name="price")],
                # absent is _sling_loaded_at, since sling introduces this column
            }
        )
    )


def test_fetch_column_metadata_failure(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
):
    with mock.patch(
        "dagster_embedded_elt.sling.resources.SlingResource.get_column_info_for_table",
        side_effect=Exception("test error"),
    ):
        from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource

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

        @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
        def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
            yield from sling.replicate(context=context).fetch_column_metadata()

        res = materialize(
            [my_sling_assets],
            resources={"sling": sling_resource},
        )

        # Assert run succeeds but no column metadata is materialized
        assert res.success
        asset_materializations = res.get_asset_materialization_events()
        assert len(asset_materializations) == 3

        metadatas = [
            asset_materialization.step_materialization_data.materialization.metadata
            for asset_materialization in asset_materializations
        ]
        assert not any(["dagster/column_schema" in metadata for metadata in metadatas]), str(
            metadatas
        )


def test_fetch_row_count(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
):
    from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource

    @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
    def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
        yield from sling.replicate(context=context).fetch_row_count()

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
    assert all(["dagster/row_count" in metadata for metadata in metadatas]), str(metadatas)

    products_key = AssetKey(["target", "main", "products"])
    products_metadata = next(
        mat for mat in asset_materializations if mat.asset_key and mat.asset_key == products_key
    ).step_materialization_data.materialization.metadata

    assert products_metadata["dagster/row_count"].value == 4


def test_fetch_row_count_failure(
    csv_to_sqlite_dataworks_replication: SlingReplicationParam,
    path_to_temp_sqlite_db: str,
):
    with mock.patch(
        "dagster_embedded_elt.sling.resources.SlingResource.get_row_count_for_table",
        side_effect=Exception("test error"),
    ):
        from dagster_embedded_elt.sling.resources import SlingConnectionResource, SlingResource

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

        @sling_assets(replication_config=csv_to_sqlite_dataworks_replication)
        def my_sling_assets(context: AssetExecutionContext, sling: SlingResource):
            yield from sling.replicate(context=context).fetch_row_count().fetch_column_metadata()

        res = materialize(
            [my_sling_assets],
            resources={"sling": sling_resource},
        )

        # Assert run succeeds but no row count metadata is attached
        assert res.success
        asset_materializations = res.get_asset_materialization_events()
        assert len(asset_materializations) == 3

        metadatas = [
            asset_materialization.step_materialization_data.materialization.metadata
            for asset_materialization in asset_materializations
        ]
        assert not any(["dagster/row_count" in metadata for metadata in metadatas]), str(metadatas)

        # Ensure subsequent column metadata is still attached
        assert all(["dagster/column_schema" in metadata for metadata in metadatas]), str(metadatas)
