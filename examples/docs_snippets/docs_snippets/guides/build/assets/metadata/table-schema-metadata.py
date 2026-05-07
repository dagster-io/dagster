import dagster as dg


# Definition-time metadata
# Here, we know the schema of the asset, so we can attach it to the asset decorator
@dg.asset(
    deps=["source_bar", "source_baz"],
    metadata={
        "dagster/column_schema": dg.TableSchema(
            columns=[
                dg.TableColumn(
                    "name",
                    "string",
                    description="The name of the person",
                ),
                dg.TableColumn(
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
@dg.asset(deps=["source_bar", "source_baz"])
def my_other_asset():
    column_names = ...
    column_types = ...

    columns = [
        dg.TableColumn(name, column_type)
        for name, column_type in zip(column_names, column_types)
    ]

    return dg.MaterializeResult(
        metadata={"dagster/column_schema": dg.TableSchema(columns=columns)}
    )
