from dagster import (
    Any, 
    Bool,
    Field,
    Float,
    Int,
    Permissive,
    Selector,
    Shape,
    String,
)
import dask.dataframe as dd


def sanitize_column_names(df: dd.DataFrame) -> dd.DataFrame:
    df.columns = map(str.lower, df.columns)
    
    return df


DataFrameUtilities = {
    "sample": {
        "function": dd.DataFrame.sample,
        "options": Shape({
            "frac": Field(Float, is_required=False, description="Fraction of axis items to return."),
            "replace": Field(Bool, is_required=False, description="Sample with or without replacement."),
            "random_state": Field(Int, is_required=False, description="Create RandomState with this as the seed."),
        }),
    },
    "set_index": {
        "function": dd.DataFrame.set_index,
        "options": Permissive({
            "other": Field(String, is_required=True, description="Set index to specified column."),
            "drop": Field(Bool, is_required=False, description="Delete columns to be used as the new index."),
            "sorted": Field(Bool, is_required=False, description="If the index column is already sorted in increasing order."),
            "divisions": Field(Any, is_required=False, description="Known values on which to separate index values of the partitions."),   
        }),
    },
    "repartition": {
        "function": dd.DataFrame.repartition,
        "options": Shape({
            "divisions": Field(Any, is_required=False, description="List of partitions to be used."),
            "npartitions": Field(Int, is_required=False, description="Number of partitions of output."),
            "partition_size": Field(Any, is_required=False, description="Max number of bytes of memory for each partition."),
            "freq": Field(String, is_required=False, description="A period on which to partition timeseries data."),
            "force": Field(Bool, is_required=False, description="Allows the expansion of the existing divisions."),
        })
    },
    "reset_index": {
        "function": dd.DataFrame.reset_index,
        "options": Shape({
            "drop": Field(Bool, is_required=False, description="Do not try to insert index into dataframe columns."),
        })
    },
    "sanitize_column_names": {
        "function": sanitize_column_names,
        "options": Field(Bool, is_required=False, description="Modify column names for greater compatibility."),   
    },
}
