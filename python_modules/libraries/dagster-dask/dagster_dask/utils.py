import re

import dask.dataframe as dd
from dagster import Any, Bool, Field, Float, Int, Permissive, Shape, String


def normalize_column_names(df: dd.DataFrame, enabled) -> dd.DataFrame:
    if enabled:
        df.columns = normalize_names(df.columns)

    return df


def normalize_names(names):
    # Based on https://stackoverflow.com/a/1176023
    camel_to_snake1 = re.compile("(.)([A-Z][a-z]+)")
    camel_to_snake2 = re.compile("([a-z0-9])([A-Z])")

    def normalize(name):
        if not name:
            return name
        name = camel_to_snake1.sub(r"\1_\2", name)
        return camel_to_snake2.sub(r"\1_\2", name).lower()

    return map(normalize, names)


DataFrameUtilities = {
    "drop": {
        "function": dd.DataFrame.drop,
        "options": Field(
            Shape(
                {
                    "labels": Field(
                        Any,
                        is_required=False,
                        description="Index or column labels to drop.",
                    ),
                    "axis": Field(
                        Any,
                        is_required=False,
                        description="Drop labesl from index or columns.",
                    ),
                    "columns": Field(
                        Any,
                        is_required=False,
                        description="Equivalent to labels with axis=1.",
                    ),
                    "errors": Field(
                        String,
                        is_required=False,
                        description='If "ignore", supress errors.',
                    ),
                }
            ),
            is_required=False,
            description="Drop specified labels from rows or columns.",
        ),
    },
    "sample": {
        "function": dd.DataFrame.sample,
        "options": Field(
            Shape(
                {
                    "frac": Field(
                        Float,
                        is_required=False,
                        description="Fraction of axis items to return.",
                    ),
                    "replace": Field(
                        Bool,
                        is_required=False,
                        description="Sample with or without replacement.",
                    ),
                    "random_state": Field(
                        Int,
                        is_required=False,
                        description="Create RandomState with this as the seed.",
                    ),
                }
            ),
            is_required=False,
            description="Random sample of items.",
        ),
    },
    "reset_index": {
        "function": dd.DataFrame.reset_index,
        "options": Field(
            Shape(
                {
                    "drop": Field(
                        Bool,
                        is_required=False,
                        description="Do not try to insert index into dataframe columns.",
                    ),
                }
            ),
            is_required=False,
            description="Reset the index to the default index.",
        ),
    },
    "set_index": {
        "function": dd.DataFrame.set_index,
        "options": Field(
            Permissive(
                {
                    "other": Field(
                        String,
                        is_required=True,
                        description="Set index to specified column.",
                    ),
                    "drop": Field(
                        Bool,
                        is_required=False,
                        description="Delete columns to be used as the new index.",
                    ),
                    "sorted": Field(
                        Bool,
                        is_required=False,
                        description="If the index column is already sorted in increasing order.",
                    ),
                    "divisions": Field(
                        Any,
                        is_required=False,
                        description=(
                            "Known values on which to separate index values of the partitions."
                        ),
                    ),
                }
            ),
            is_required=False,
            description="Set the DataFrame index using an existing column.",
        ),
    },
    "repartition": {
        "function": dd.DataFrame.repartition,
        "options": Field(
            Shape(
                {
                    "divisions": Field(
                        Any,
                        is_required=False,
                        description="List of partitions to be used.",
                    ),
                    "npartitions": Field(
                        Int,
                        is_required=False,
                        description="Number of partitions of output.",
                    ),
                    "partition_size": Field(
                        Any,
                        is_required=False,
                        description="Max number of bytes of memory for each partition.",
                    ),
                    "freq": Field(
                        String,
                        is_required=False,
                        description="A period on which to partition timeseries data.",
                    ),
                    "force": Field(
                        Bool,
                        is_required=False,
                        description="Allows the expansion of the existing divisions.",
                    ),
                }
            ),
            is_required=False,
            description="Repartition dataframe along new divisions.",
        ),
    },
    "normalize_column_names": {
        "function": normalize_column_names,
        "options": Field(
            Bool,
            is_required=False,
            description="Lowercase and convert CamelCase to snake_case on column names.",
        ),
    },
}


def apply_utilities_to_df(df, config):
    for util_name, util_spec in DataFrameUtilities.items():
        if util_name in config:
            util_func = util_spec["function"]
            util_opts = config[util_name]

            if isinstance(util_opts, dict):
                df = util_func(df, **util_opts)
            elif isinstance(util_opts, list):
                df = util_func(df, *util_opts)
            else:
                df = util_func(df, util_opts)

    return df
