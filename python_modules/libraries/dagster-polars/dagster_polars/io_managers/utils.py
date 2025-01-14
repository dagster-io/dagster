import json
from collections.abc import Mapping
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pprint import pformat
from typing import Any, Optional, Union

import polars as pl
from dagster import (
    MetadataValue,
    OutputContext,
    TableColumn,
    TableMetadataValue,
    TableRecord,
    TableSchema,
)

POLARS_DATA_FRAME_ANNOTATIONS = [
    Any,
    pl.DataFrame,
    dict[str, pl.DataFrame],
    Mapping[str, pl.DataFrame],
    type(None),
    None,
    dict[str, pl.DataFrame],
]

POLARS_LAZY_FRAME_ANNOTATIONS = [
    pl.LazyFrame,
    dict[str, pl.LazyFrame],
    Mapping[str, pl.LazyFrame],
    dict[str, pl.DataFrame],
]


def cast_polars_single_value_to_dagster_table_types(val: Any):
    if val is None:
        return ""
    elif isinstance(val, (date, datetime, time, timedelta, bytes)):
        return str(val)
    elif isinstance(val, (list, dict)):
        # default=str because sometimes the object can be a list of datetimes or something like this
        return json.dumps(val, default=str)
    elif isinstance(val, Decimal):
        return float(val)
    else:
        return val


def get_metadata_schema(
    df: Union[pl.DataFrame, pl.LazyFrame],
    descriptions: Optional[dict[str, str]] = None,
) -> TableSchema:
    """Takes the schema from a dataframe or lazyframe and converts it a Dagster TableSchema.

    Args:
        df (Union[pl.DataFrame, pl.LazyFrame]): dataframe
        descriptions (Optional[Dict[str, str]], optional): column descriptions. Defaults to None.

    Returns:
        TableSchema: dagster TableSchema
    """
    descriptions = descriptions or {}
    return TableSchema(
        columns=[
            TableColumn(name=col, type=str(pl_type), description=descriptions.get(col))
            for col, pl_type in df.collect_schema().items()
        ]
    )


def get_table_metadata(
    context: OutputContext,
    df: pl.DataFrame,
    schema: Optional[TableSchema] = None,
    n_rows: Optional[int] = 5,
    fraction: Optional[float] = None,
) -> Optional[TableMetadataValue]:
    """Takes the polars DataFrame and takes a sample of the data and returns it as TableMetaDataValue.
    With LazyFrame this is not possible without doing possible a very costly operation.

    Args:
        context (OutputContext): output context
        df (pl.DataFrame): polars frame
        schema (Optional[TableSchema]): dataframe schema
        n_rows (Optional[int]): number of rows to sample from. Defaults to 5.
        fraction (Optional[float]): fraction of rows to sample from. Defaults to None.
        with_schema (bool): if to include the schema in the metadata

    Returns:
        Tuple[TableSchema, Optional[TableMetadataValue]]: schema metadata, and optional sample metadata
    """
    if n_rows is not None:
        n_rows = min(n_rows, len(df))

    if fraction is not None or n_rows is not None:
        df_sample = df.sample(n=n_rows, fraction=fraction, shuffle=True)
    else:
        df_sample = df

    try:
        # this can fail sometimes
        # because TableRecord doesn't support all python types
        df_sample_dict = df_sample.to_dicts()

        table = MetadataValue.table(
            records=[
                TableRecord(
                    {
                        col: cast_polars_single_value_to_dagster_table_types(df_sample_dict[i][col])
                        for col in df.columns
                    }
                )
                for i in range(len(df_sample))
            ],
            schema=schema,
        )
    except TypeError as e:
        context.log.error(
            f"Failed to create table sample metadata."
            f"Reason:\n{e}\n"
            f"Schema:\n{df.schema}\n"
            f"Polars sample:\n{df_sample}\n"
            f"dict sample:\n{pformat(df_sample.to_dicts())}"
        )
        return None
    return table


def get_polars_metadata(
    context: OutputContext, df: Union[pl.DataFrame, pl.LazyFrame]
) -> dict[str, MetadataValue]:
    """Retrives some metadata on polars frames
    - DataFrame: stats, row_count, table or schema
    - LazyFrame: schema.

    Args:
        context (OutputContext): context
        df (Union[pl.DataFrame, pl.LazyFrame]): output dataframe

    Returns:
        Dict[str, MetadataValue]: metadata about df
    """
    assert context.definition_metadata is not None

    schema_metadata = get_metadata_schema(
        df, descriptions=context.definition_metadata.get("descriptions")
    )

    metadata = {}

    metadata["dagster/column_schema"] = schema_metadata

    if isinstance(df, pl.DataFrame):
        table_metadata = get_table_metadata(
            context=context,
            df=df,
            schema=schema_metadata,
            n_rows=context.definition_metadata.get("n_rows", 5),
            fraction=context.definition_metadata.get("fraction"),
        )

        df_stats = df.describe()

        stats_metadata = get_table_metadata(
            context=context,
            df=df_stats,
            n_rows=None,
            fraction=None,
        )

        metadata["table"] = table_metadata
        metadata["stats"] = stats_metadata
        metadata["dagster/row_count"] = MetadataValue.int(df.shape[0])
        metadata["estimated_size_mb"] = MetadataValue.float(df.estimated_size(unit="mb"))

    return metadata
