from dagster import (
    MaterializeResult,
    TableColumn,
    TableSchema,
    asset,
)


# Definition-time metadata
# Here, we know the schema of the asset, so we can attach it to the asset decorator
@asset(
    deps=["source_bar", "source_baz"],
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


# Runtime metadata
# Here, the schema isn't known until the asset is materialized
@asset(deps=["source_bar", "source_baz"])
def my_other_asset():
    column_names = ...
    column_types = ...

    columns = [
        TableColumn(name, column_type)
        for name, column_type in zip(column_names, column_types)
    ]

    return MaterializeResult(
        metadata={
            "dagster/column_schema": TableSchema(columns=columns)
        }
    )