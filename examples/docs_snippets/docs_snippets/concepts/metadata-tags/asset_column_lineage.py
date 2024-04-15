from dagster import (
    AssetKey,
    MaterializeResult,
    TableColumnDep,
    TableColumnLineage,
    asset,
)


@asset(deps=[AssetKey("source_bar"), AssetKey("source_baz")])
def my_asset():
    yield MaterializeResult(
        metadata={
            "dagster/column_lineage": TableColumnLineage(
                deps_by_column={
                    "new_column_foo": [
                        TableColumnDep(
                            asset_key=AssetKey("source_bar"),
                            column_name="column_bar",
                        ),
                        TableColumnDep(
                            asset_key=AssetKey("source_baz"),
                            column_name="column_baz",
                        ),
                    ],
                    "new_column_qux": [
                        TableColumnDep(
                            asset_key=AssetKey("source_bar"),
                            column_name="column_quuz",
                        ),
                    ],
                }
            )
        }
    )
