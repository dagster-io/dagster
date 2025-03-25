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
def patito_model_to_dagster_type(
    model: pt.Model | Any,
    description: str | None = None,
) -> DagsterType:  # noqa: ANN401
    """Convert patito model to dagster type checking.

    Args:
        model (pt.Model): validation model of frame
        dagster_type_suffix (str): the dagster type name suffix, to avoid duplication of dagster type names in case of multiple assets sharing a patito model. Defaults to None
        description (str): Dagster Type description

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
    description = f"Dagster Type constructor for Polars DataFrame conforming to Patito model {model.__class__.__name__}"

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
        name=model.__class__.__name__,
        metadata={
            "schema": MetadataValue.table_schema(table_schema),
        },
        typing_type=pl.DataFrame,
        description=description,
    )


def _patito_model_to_type_check_fn(
    schema: pt.Model,
) -> Callable[[TypeCheckContext, object], TypeCheck]:
    def type_check_fn(context: TypeCheckContext, value: object) -> TypeCheck:  # noqa: ARG001
        if isinstance(value, VALID_DATAFRAME_CLASSES):
            try:
                schema.validate(value)
                return TypeCheck(success=True)
            except pt.DataFrameValidationError as e:
                return TypeCheck(
                    success=False,
                    description=str(e),
                )
        else:
            return TypeCheck(
                success=False,
                description=(
                    f"Must be one of {VALID_DATAFRAME_CLASSES}, not {type(value).__name__}."
                ),
            )

    return type_check_fn
