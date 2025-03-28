import dagster as dg


@dg.asset(deps=["source_bar", "source_baz"])
def my_asset():
    # The following TableColumnLineage models 3 tables:
    # source_bar, source_baz, and my_asset
    # With the following column dependencies:
    # - my_asset.new_column_foo depends on:
    #   - source_bar.column_bar
    #   - source_baz.column_baz
    # - my_asset.new_column_qux depends on:
    #   - source_bar.column_quuz
    return dg.MaterializeResult(
        metadata={
            "dagster/column_lineage": dg.TableColumnLineage(
                deps_by_column={
                    "new_column_foo": [
                        dg.TableColumnDep(
                            asset_key=dg.AssetKey("source_bar"),
                            column_name="column_bar",
                        ),
                        dg.TableColumnDep(
                            asset_key=dg.AssetKey("source_baz"),
                            column_name="column_baz",
                        ),
                    ],
                    "new_column_qux": [
                        dg.TableColumnDep(
                            asset_key=dg.AssetKey("source_bar"),
                            column_name="column_quuz",
                        ),
                    ],
                }
            )
        }
    )
