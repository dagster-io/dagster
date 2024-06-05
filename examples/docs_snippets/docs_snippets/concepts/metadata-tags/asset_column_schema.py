from dagster import AssetKey, MaterializeResult, TableColumn, TableSchema, asset


# Definition metadata
# Here, we know the schema of the asset, so we can attach it to the asset decorator
@asset(
    deps=[AssetKey("source_bar"), AssetKey("source_baz")],
    metadata={
        "dagster/column_schema": TableSchema(
            columns=[
                TableColumn(
                    "name",
                    "string",
                    description="The name of the person",
                ),
                TableColumn(
                    "age",
                    "int",
                    description="The age of the person",
                ),
            ]
        )
    },
)
def my_asset(): ...


# Materialization metadata
# Here, the schema isn't known until runtime
@asset(deps=[AssetKey("source_bar"), AssetKey("source_baz")])
def my_other_asset():
    column_names = ...
    column_types = ...

    columns = [
        TableColumn(name, column_type)
        for name, column_type in zip(column_names, column_types)
    ]

    yield MaterializeResult(
        metadata={"dagster/column_schema": TableSchema(columns=columns)}
    )
