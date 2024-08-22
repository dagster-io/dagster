from dagster import (
    AssetKey,
    MaterializeResult,
    TableColumnDep,
    TableColumnLineage,
    asset,
)


@asset(deps=["source_bar", "source_baz"])
def my_asset():
    # The following TableColumnLineage models 3 tables:
    # source_bar, source_baz, and my_asset
    # With the following column dependencies:
    # - my_asset.new_column_foo depends on:
    #   - source_bar.column_bar
    #   - source_baz.column_baz
    # - my_asset.new_column_qux depends on:
    #   - source_bar.column_quuz
    return MaterializeResult(
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