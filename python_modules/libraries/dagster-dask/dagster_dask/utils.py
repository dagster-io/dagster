from dagster import (
    Any, 
    Bool,
    Field,
    Int,
    Permissive,
    Selector,
    String,
)
import dask.dataframe as dd


def sanitize_column_names(df: dd.DataFrame) -> dd.DataFrame:
    df.columns = map(str.lower, df.columns)
    
    return df


DataFrameUtilities = {
    "sample": {
        "function": dd.DataFrame.sample,
        "options": Field(Float, is_required=False, description="Sample a random fraction of items.")
    },
    "repartition": {
        "function": dd.DataFrame.repartition,
        "options": Field(
            Selector(
                {
                    "npartitions": Field(Int, description="Number of partitions of output."),
                    "partition_size": Field(Any, description="Max number of bytes of memory for each partition."),
                }
            ),
            is_required=False,
            description="Repartition dataframe along new divisions.",
        )  
    },
    "reset_index": {
        "function": dd.DataFrame.reset_index,
        "options": Field(Bool, is_required=False, description="Reset the index to the default index."),
    },
    "sanitize_column_names": {
        "function": sanitize_column_names,
        "options": Field(Bool, is_required=False, description="Modify column names for greater compatibility."),   
    }
}
