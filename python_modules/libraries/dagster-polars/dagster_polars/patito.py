from collections.abc import Callable
from typing import TYPE_CHECKING, Optional

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

if TYPE_CHECKING:
    import patito as pt

VALID_DATAFRAME_CLASSES = (pl.DataFrame,)


def get_patito_metadata(model: type["pt.Model"]) -> dict[str, MetadataValue]:
    """Extracts Dagster metadata from a Patito model."""
    table_columns = []
    schema_dtypes: dict = model.dtypes
    column_infos: dict = model.column_infos

    for col, properties in model._schema_properties().items():  # noqa: SLF001
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

    return {
        "dagster/column_schema": MetadataValue.table_schema(table_schema),
    }


def patito_model_to_dagster_type(
    model: type["pt.Model"],
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> DagsterType:
    """Convert patito model to dagster type checking.

    Logs Dagster metadata associated with the Patito model, such as `dagster/column_schema`.

    Args:
        model (type[pt.Model]): the Patito model
        name (str): Dagster Type name. Defaults to the model class name.
        description (str): Dagster Type description. By default it references the model class name.

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
    type_check_fn = _patito_model_to_type_check_fn(model)
    return DagsterType(
        type_check_fn=type_check_fn,
        name=model.__class__.__name__,
        metadata=get_patito_metadata(model),
        typing_type=model.DataFrame,
        description=description
        or f"Polars frame conforming to Patito model {model.__class__.__name__}",
    )


def _patito_model_to_type_check_fn(
    model: "pt.Model",
) -> Callable[[TypeCheckContext, object], TypeCheck]:
    import patito as pt

    def type_check_fn(context: TypeCheckContext, value: object) -> TypeCheck:
        if isinstance(value, VALID_DATAFRAME_CLASSES):
            try:
                model.validate(value)
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
