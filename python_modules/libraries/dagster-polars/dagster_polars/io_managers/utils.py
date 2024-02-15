import json
import sys
from datetime import date, datetime, time, timedelta
from pprint import pformat
from typing import Any, Dict, Mapping, Optional, Union

import polars as pl
from dagster import (
    MetadataValue,
    OutputContext,
    TableColumn,
    TableMetadataValue,
    TableRecord,
    TableSchema,
)
from packaging.version import Version

POLARS_DATA_FRAME_ANNOTATIONS = [
    Any,
    pl.DataFrame,
    Dict[str, pl.DataFrame],
    Mapping[str, pl.DataFrame],
    type(None),
    None,
]

POLARS_LAZY_FRAME_ANNOTATIONS = [
    pl.LazyFrame,
    Dict[str, pl.LazyFrame],
    Mapping[str, pl.LazyFrame],
]


if sys.version >= "3.9":
    POLARS_DATA_FRAME_ANNOTATIONS.append(dict[str, pl.DataFrame])  #  type: ignore # ignore needed with Python < 3.9
    POLARS_LAZY_FRAME_ANNOTATIONS.append(dict[str, pl.DataFrame])  #  type: ignore # ignore needed with Python < 3.9


def cast_polars_single_value_to_dagster_table_types(val: Any):
    if val is None:
        return ""
    elif isinstance(val, (date, datetime, time, timedelta, bytes)):
        return str(val)
    elif isinstance(val, (list, dict)):
        # default=str because sometimes the object can be a list of datetimes or something like this
        return json.dumps(val, default=str)
    else:
        return val


def get_metadata_schema(
    df: Union[pl.DataFrame, pl.LazyFrame],
    descriptions: Optional[Dict[str, str]] = None,
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
            for col, pl_type in df.schema.items()
        ]
    )


def get_table_metadata(
    context: OutputContext,
    df: pl.DataFrame,
    schema: TableSchema,
    n_rows: Optional[int] = 5,
    fraction: Optional[float] = None,
) -> Optional[TableMetadataValue]:
    """Takes the polars DataFrame and takes a sample of the data and returns it as TableMetaDataValue.
    A lazyframe this is not possible without doing possible a very costly operation.

    Args:
        context (OutputContext): output context
        df (pl.DataFrame): polars frame
        schema (TableSchema): dataframe schema,
        n_rows (Optional[int], optional): number of rows to sample from. Defaults to 5.
        fraction (Optional[float], optional): fraction of rows to sample from. Defaults to None.

    Returns:
        Tuple[TableSchema, Optional[TableMetadataValue]]: schema metadata, and optional sample metadata
    """
    assert not fraction and n_rows, "only one of n_rows and frac should be set"
    n_rows = min(n_rows, len(df))
    df_sample = df.sample(n=n_rows, fraction=fraction, shuffle=True)

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


def get_polars_df_stats(
    df: pl.DataFrame,
) -> Dict[str, Dict[str, Union[str, int, float]]]:
    describe = df.describe().fill_null(pl.lit("null"))
    # TODO(ion): replace once there is a index column selector
    if Version(pl.__version__) >= Version("0.20.6"):
        col_name = "statistic"
    else:
        col_name = "describe"
    return {
        col: {stat: describe[col][i] for i, stat in enumerate(describe[col_name].to_list())}
        for col in describe.columns[1:]
    }


def get_polars_metadata(
    context: OutputContext, df: Union[pl.DataFrame, pl.LazyFrame]
) -> Dict[str, MetadataValue]:
    """Retrives some metadata on polars frames
    - DataFrame: stats, row_count, table or schema
    - LazyFrame: schema.

    Args:
        context (OutputContext): context
        df (Union[pl.DataFrame, pl.LazyFrame]): output dataframe

    Returns:
        Dict[str, MetadataValue]: metadata about df
    """
    assert context.metadata is not None

    schema = get_metadata_schema(df, descriptions=context.metadata.get("descriptions"))

    metadata = {}

    if isinstance(df, pl.DataFrame):
        table = get_table_metadata(
            context=context,
            df=df,
            schema=schema,
            n_rows=context.metadata.get("n_rows", 5),
            fraction=context.metadata.get("fraction"),
        )
        metadata["stats"] = MetadataValue.json(get_polars_df_stats(df))
        metadata["row_count"] = MetadataValue.int(df.shape[0])
    else:
        table = None

    if table is not None:
        metadata["table"] = table
    else:
        metadata["schema"] = schema

    return metadata
