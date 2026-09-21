import dagster as dg


@dg.asset(deps=[dg.AssetKey("source_bar"), dg.AssetKey("source_baz")])
def my_asset():
    yield dg.MaterializeResult(
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
