import json
import sys
from datetime import date, datetime, time, timedelta
from pprint import pformat
from typing import Any, Dict, Mapping, Optional, Tuple, Union

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
    POLARS_DATA_FRAME_ANNOTATIONS.append(dict[str, pl.DataFrame])  # type: ignore
    POLARS_LAZY_FRAME_ANNOTATIONS.append(dict[str, pl.DataFrame])  # type: ignore


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
    df: pl.DataFrame,
    descriptions: Optional[Dict[str, str]] = None,
):
    descriptions = descriptions or {}
    return TableSchema(
        columns=[
            TableColumn(name=col, type=str(pl_type), description=descriptions.get(col))
            for col, pl_type in df.schema.items()
        ]
    )


def get_metadata_table_and_schema(
    context: OutputContext,
    df: pl.DataFrame,
    n_rows: Optional[int] = 5,
    fraction: Optional[float] = None,
    descriptions: Optional[Dict[str, str]] = None,
) -> Tuple[TableSchema, Optional[TableMetadataValue]]:
    assert not fraction and n_rows, "only one of n_rows and frac should be set"
    n_rows = min(n_rows, len(df))

    schema = get_metadata_schema(df, descriptions=descriptions)

    df_sample = df.sample(n=n_rows, fraction=fraction, shuffle=True)

    try:
        # this can fail sometimes
        # because TableRecord doesn't support all python types
        df_sample_dict = df_sample.to_dicts()
        table = MetadataValue.table(
            records=[
                TableRecord(
                    {
                        col: cast_polars_single_value_to_dagster_table_types(df_sample_dict[i][col])  # type: ignore
                        for col in df.columns
                    }
                )
                for i in range(len(df_sample))
            ],
            schema=schema,
        )

    except TypeError as e:
        context.log.error(
            f"Failed to create table sample metadata. Will only record table schema metadata. "
            f"Reason:\n{e}\n"
            f"Schema:\n{df.schema}\n"
            f"Polars sample:\n{df_sample}\n"
            f"dict sample:\n{pformat(df_sample.to_dicts())}"
        )
        return schema, None

    return schema, table


def get_polars_df_stats(
    df: pl.DataFrame,
) -> Dict[str, Dict[str, Union[str, int, float]]]:
    describe = df.describe().fill_null(pl.lit("null"))
    return {
        col: {stat: describe[col][i] for i, stat in enumerate(describe["describe"].to_list())}
        for col in describe.columns[1:]
    }


def get_polars_metadata(context: OutputContext, df: pl.DataFrame) -> Dict[str, MetadataValue]:
    assert context.metadata is not None
    schema, table = get_metadata_table_and_schema(
        context=context,
        df=df,
        n_rows=context.metadata.get("n_rows", 5),
        fraction=context.metadata.get("fraction"),
        descriptions=context.metadata.get("descriptions"),
    )

    metadata = {
        "stats": MetadataValue.json(get_polars_df_stats(df)),
        "row_count": MetadataValue.int(len(df)),
    }

    if table is not None:
        metadata["table"] = table
    else:
        metadata["schema"] = schema

    return metadata
