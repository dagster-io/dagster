from collections.abc import Callable
from typing import Any

import patito as pt
import polars as pl
from dagster import (
    DagsterType,
    MetadataValue,
    TableColumn,
    TableColumnConstraints,
    TableSchema,
    TypeCheck,
    TypeCheckContext,
)

VALID_DATAFRAME_CLASSES = (pl.DataFrame,)


# TODO: look into a better way to get the asset name and pass it to this function
def patito_model_to_dagster_type(model: pt.Model | Any, asset_name: str) -> DagsterType:  # noqa: ANN401
    """Convert patito model to dagster type checking.

    Args:
        model (pt.Model): validation model of frame

    Returns:
        DagsterType: Dagster type with patito validation fn

    Example:
    ```python
    class MyTable(pt.Model):
        col_1: str | None
        col_2: int = pt.Field(unique=True)

    @asset(dagster_type=patito_model_to_dagster_type(MyTable, "my_asset"),
        io_manager_key="my_io_manager")
    def my_asset() -> pl.DataFrame:
        return pl.DataFrame({
            "col_1": ['a'],
            "col_2": [2],
        })
    ```
    """
    table_columns = []
    schema_dtypes: dict = model.dtypes
    column_infos: dict = model.column_infos

    for col, properties in model._schema_properties().items():
        table_columns.append(
            TableColumn(
                name=col,
                type=str(schema_dtypes[col]),
                constraints=TableColumnConstraints(
                    unique=column_infos[col].unique
                    if column_infos[col].unique is not None
                    else False,
                    nullable="anyOf" in properties,
                    # TODO: Handle Other constraints, serialize the expressions
                ),
            ),
        )
    table_schema = TableSchema(columns=table_columns)

    type_check_fn = _patito_model_to_type_check_fn(model)
    return DagsterType(
        type_check_fn=type_check_fn,
        name=asset_name,
        metadata={
            "schema": MetadataValue.table_schema(table_schema),
        },
        typing_type=pl.DataFrame,
    )


def _patito_model_to_type_check_fn(
    schema: pt.Model,
) -> Callable[[TypeCheckContext, object], TypeCheck]:
    def type_check_fn(context: TypeCheckContext, value: object) -> TypeCheck:  # noqa: ARG001
        if isinstance(value, VALID_DATAFRAME_CLASSES):
            try:
                schema.validate(value)
            except pt.DataFrameValidationError as e:
                return TypeCheck(
                    success=False,
                    description=str(e),
                )
            except Exception as e:
                return TypeCheck(
                    success=False,
                    description=f"Unexpected error during validation: {e}",
                )
        else:
            return TypeCheck(
                success=False,
                description=(
                    f"Must be one of {VALID_DATAFRAME_CLASSES}, not {type(value).__name__}."
                ),
            )
        return TypeCheck(success=True)

    return type_check_fn
