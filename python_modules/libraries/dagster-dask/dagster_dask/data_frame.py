import contextlib

import dask.dataframe as dd
from dagster import (
    Any,
    AssetMaterialization,
    Bool,
    DagsterInvariantViolationError,
    DagsterType,
    Enum,
    EnumValue,
    EventMetadataEntry,
    Field,
    Int,
    Permissive,
    Selector,
    Shape,
    String,
    TypeCheck,
    check,
    dagster_type_loader,
    dagster_type_materializer,
)

from .utils import DataFrameUtilities, apply_utilities_to_df

WriteCompressionTextOptions = Enum(
    "WriteCompressionText",
    [
        EnumValue("gzip"),
        EnumValue("bz2"),
        EnumValue("xz"),
    ],
)

EngineParquetOptions = Enum(
    "EngineParquet",
    [
        EnumValue("auto"),
        EnumValue("fastparquet"),
        EnumValue("pyarrow"),
    ],
)


DataFrameReadTypes = {
    "csv": {
        "function": dd.read_csv,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "blocksize": (Any, False, "Number of bytes by which to cut up larger files."),
            "sample": (Int, False, "Number of bytes to use when determining dtypes."),
            "assume_missing": (
                Bool,
                False,
                "If True, all integer columns that aren’t specified in `dtype` are assumed to contain missing values, and are converted to floats.",
            ),
            "storage_options": (
                Permissive(),
                False,
                "Extra options that make sense for a particular storage connection.",
            ),
            "include_path_column": (
                Any,
                False,
                "Whether or not to include the path to each particular file.",
            ),
        },
    },
    "parquet": {
        "function": dd.read_parquet,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "columns": (Any, False, "Field name(s) to read in as columns in the output."),
            "filters": (Any, False, "List of filters to apply."),
            "index": (Any, False, "Field name(s) to use as the output frame index."),
            "categories": (
                Any,
                False,
                "For any fields listed here, if the parquet encoding is Dictionary, the column will be created with dtype category.",
            ),
            "storage_options": (
                Permissive(),
                False,
                "Key/value pairs to be passed on to the file-system backend, if any.",
            ),
            "engine": (EngineParquetOptions, False, "Parquet reader library to use."),
            "gather_statistics": (Bool, False, "Gather the statistics for each dataset partition."),
            "split_row_groups": (
                Bool,
                False,
                "If True (default) then output dataframe partitions will correspond to parquet-file row-groups.",
            ),
            "chunksize": (Any, False, "The target task partition size."),
        },
    },
    "hdf": {
        "function": dd.read_hdf,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "key": (Any, True, "The group identifier in the store."),
            "start": (Int, False, "Row number to start selection."),
            "stop": (Int, False, "Row number to stop selection."),
            "columns": (list, False, "A list of columns names to return."),
            "chunksize": (Any, False, "Maximal number of rows per partition."),
            "sorted_index": (
                Bool,
                False,
                "Option to specify whether or not the input hdf files have a sorted index.",
            ),
            "lock": (Bool, False, "Option to use a lock to prevent concurrency issues."),
            "mode": (String, False, "Mode to use when opening file(s)."),
        },
    },
    "json": {
        "function": dd.read_json,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "encoding": (String, False, "The text encoding to implement."),
            "errors": (String, False, "How to respond to errors in the conversion."),
            "storage_options": (
                Permissive(),
                False,
                "Passed to backend file-system implementation.",
            ),
            "blocksize": (Int, False, "Each partition will be approximately this size in bytes."),
            "sample": (
                Int,
                False,
                "Number of bytes to pre-load, to provide an empty dataframe structure to any blocks without data.",
            ),
            "compression": (String, False, "String like ‘gzip’ or ‘xz’."),
        },
    },
    "sql_table": {
        "function": dd.read_sql_table,
        "is_path_based": False,
        "options": {
            "table": (Any, True, "Select columns from here."),
            "uri": (String, True, "Full sqlalchemy URI for the database connection."),
            "index_col": (
                String,
                True,
                "Column which becomes the index, and defines the partitioning.",
            ),
            "divisions": (Any, False, "Values of the index column to split the table by."),
            "npartitions": (Int, False, "Number of partitions, if divisions is not given."),
            "columns": (Any, False, "Which columns to select."),
            "bytes_per_chunk": (Any, False, "The target size of each partition, in bytes."),
            "head_rows": (
                Int,
                False,
                "How many rows to load for inferring the data-types, unless passing meta.",
            ),
            "schema": (
                String,
                False,
                "If using a table name, pass this to sqlalchemy to select which DB schema to use within the URI connection.",
            ),
        },
    },
    "table": {
        "function": dd.read_table,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "blocksize": (Any, False, "Number of bytes by which to cut up larger files."),
            "sample": (Int, False, "Number of bytes to use when determining dtypes."),
            "assume_missing": (
                Bool,
                False,
                "If True, all integer columns that aren’t specified in dtype are assumed to contain missing values, and are converted to floats.",
            ),
            "storage_options": (
                Permissive(),
                False,
                "Extra options that make sense for a particular storage connection.",
            ),
            "include_path_column": (
                Any,
                False,
                "Whether or not to include the path to each particular file.",
            ),
        },
    },
    "fwf": {
        "function": dd.read_fwf,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "blocksize": (Any, False, "Number of bytes by which to cut up larger files."),
            "sample": (Int, False, "Number of bytes to use when determining dtypes."),
            "assume_missing": (
                Bool,
                False,
                "If True, all integer columns that aren’t specified in dtype are assumed to contain missing values, and are converted to floats.",
            ),
            "storage_options": (
                Permissive(),
                False,
                "Extra options that make sense for a particular storage connection.",
            ),
            "include_path_column": (
                Any,
                False,
                "Whether or not to include the path to each particular file.",
            ),
        },
    },
    "orc": {
        "function": dd.read_orc,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "columns": (Any, False, "Columns to load."),
            "storage_options": (
                Permissive(),
                False,
                "Further parameters to pass to the bytes backend.",
            ),
        },
    },
}


DataFrameToTypes = {
    "csv": {
        "function": dd.DataFrame.to_csv,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Path glob indicating the naming scheme for the output files"),
            "single_file": (Bool, False, "Whether to save everything into a single CSV file."),
            "encoding": (
                String,
                False,
                "A string representing the encoding to use in the output file.",
            ),
            "mode": (String, False, "Python write mode."),
            "compression": (
                WriteCompressionTextOptions,
                False,
                "A string representing the compression to use in the output file.",
            ),
            "compute_kwargs": (
                Permissive(),
                False,
                "Options to be passed in to the compute method.",
            ),
        },
    },
    "parquet": {
        "function": dd.DataFrame.to_parquet,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Destination directory for data."),
            "engine": (EngineParquetOptions, False, "Parquet library to use."),
            "compression": (
                Any,
                False,
                'Either a string like ``"snappy"`` or a dictionary mapping column names to compressors like ``{"name": "gzip", "values": "snappy"}``.',
            ),
            "write_index": (Bool, False, "Whether or not to write the index."),
            "append": (Bool, False, "Whether to add new row-group(s) to an existing data-set."),
            "ignore_divisions": (
                Bool,
                False,
                "If False (default) raises error when previous divisions overlap with the new appended divisions.",
            ),
            "partition_on": (
                list,
                False,
                "onstruct directory-based partitioning by splitting on these fields values.",
            ),
            "storage_options": (
                Permissive(),
                False,
                "Key/value pairs to be passed on to the file-system backend, if any.",
            ),
            "write_metadata_file": (
                Bool,
                False,
                "Whether to write the special ``_metadata`` file.",
            ),
            "compute_kwargs": (
                Permissive(),
                False,
                "Options to be passed in to the compute method.",
            ),
        },
    },
    "hdf": {
        "function": dd.DataFrame.to_hdf,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Path to a target filename."),
            "key": (String, True, "Datapath within the files."),
            "scheduler": (String, False, 'The scheduler to use, like "threads" or "processes".'),
        },
    },
    "json": {
        "function": dd.DataFrame.to_json,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Location to write to."),
            "encoding": (String, False, "The text encoding to implement."),
            "errors": (String, False, "How to respond to errors in the conversion."),
            "storage_options": (
                Permissive(),
                False,
                "Passed to backend file-system implementation.",
            ),
            "compute_kwargs": (
                Permissive(),
                False,
                "Options to be passed in to the compute method.",
            ),
            "compression": (String, False, 'String like "gzip" or "xz".'),
        },
    },
    "sql": {
        "function": dd.DataFrame.to_sql,
        "is_path_based": False,
        "options": {
            "name": (String, True, "Name of SQL table."),
            "uri": (String, True, "Full sqlalchemy URI for the database connection."),
            "schema": (String, False, "Specify the schema (if database flavor supports this)."),
            "if_exists": (String, False, "How to behave if the table already exists."),
            "index": (Bool, False, "Write DataFrame index as a column."),
            "index_label": (Any, False, "Column label for index column(s)."),
            "chunksize": (
                Int,
                False,
                "Specify the number of rows in each batch to be written at a time.",
            ),
            "dtype": (Any, False, "Specifying the datatype for columns."),
            "method": (String, False, "Controls the SQL insertion clause used."),
            "parallel": (
                Bool,
                False,
                "When true, have each block append itself to the DB table concurrently.",
            ),
        },
    },
}


def _dataframe_loader_config():
    read_fields = {
        read_from: Permissive(
            {
                option_name: Field(
                    option_args[0], is_required=option_args[1], description=option_args[2]
                )
                for option_name, option_args in read_opts["options"].items()
            }
        )
        for read_from, read_opts in DataFrameReadTypes.items()
    }

    return Shape(
        {
            "read": Field(
                Selector(read_fields),
            ),
            **{
                util_name: util_spec["options"]
                for util_name, util_spec in DataFrameUtilities.items()
            },
        }
    )


@dagster_type_loader(_dataframe_loader_config())
def dataframe_loader(_context, config):
    read_type, read_options = next(iter(config["read"].items()))

    if not read_type:
        raise DagsterInvariantViolationError("No read_type found. Expected read key in config.")
    if not read_type in DataFrameReadTypes:
        raise DagsterInvariantViolationError(
            "Unsupported read_type {read_type}.".format(read_type=read_type)
        )

    # Get the metadata entry for the read_type in order to know which function
    # to call and whether it uses path as the first argument. And, make
    # read_options mutable if we need to pop off a path argument.
    read_meta = DataFrameReadTypes[read_type]
    read_options = dict(read_options)

    # Get the read function and prepare its arguments.
    read_function = read_meta["function"]
    read_args = [read_options.pop("path")] if read_meta.get("is_path_based", False) else []
    read_kwargs = read_options

    # Read the dataframe and apply any utility functions
    df = read_function(*read_args, **read_kwargs)
    df = apply_utilities_to_df(df, config)
    df = df.persist()

    return df


def _dataframe_materializer_config():
    to_fields = {
        write_to: Permissive(
            {
                option_name: Field(
                    option_args[0], is_required=option_args[1], description=option_args[2]
                )
                for option_name, option_args in to_opts["options"].items()
            }
        )
        for write_to, to_opts in DataFrameToTypes.items()
    }

    return Shape(
        {
            "to": Field(
                Selector(to_fields),
            ),
            **{
                util_name: util_spec["options"]
                for util_name, util_spec in DataFrameUtilities.items()
            },
        }
    )


@dagster_type_materializer(_dataframe_materializer_config())
def dataframe_materializer(_context, config, dask_df):
    check.inst_param(dask_df, "dask_df", dd.DataFrame)

    to_specs = config["to"]

    # Apply any utility functions in preparation for materialization
    dask_df = apply_utilities_to_df(dask_df, config)
    dask_df = dask_df.persist()

    # Materialize to specified types
    for to_type, to_options in to_specs.items():
        if not to_type in DataFrameToTypes:
            check.failed("Unsupported to_type {to_type}".format(to_type=to_type))

        # Get the metadata entry for the read_type in order to know which method
        # to call and whether it uses path as the first argument. And, make
        # to_options mutable if we need to pop off a path argument.
        to_meta = DataFrameToTypes[to_type]
        to_options = dict(to_options)

        # Get the to function and prepare its arguments.
        to_function = to_meta["function"]
        to_path = to_options.pop("path") if to_meta.get("is_path_based", False) else None
        to_args = [to_path] if to_path else []
        to_kwargs = to_options

        # Get the Dask client from the dask resource, if available.
        client_context = (
            _context.resources.dask.client.as_current()
            if hasattr(_context.resources, "dask")
            else contextlib.suppress()
        )
        with client_context:
            to_function(dask_df, *to_args, **to_kwargs)

        if to_path:
            yield AssetMaterialization.file(to_path)


def df_type_check(_, value):
    if not isinstance(value, dd.DataFrame):
        return TypeCheck(success=False)
    return TypeCheck(
        success=True,
        metadata_entries=[
            # string cast columns since they may be things like datetime
            EventMetadataEntry.json({"columns": list(map(str, value.columns))}, "metadata"),
        ],
    )


DataFrame = DagsterType(
    name="DaskDataFrame",
    description="""A Dask DataFrame is a large parallel DataFrame composed of many smaller Pandas DataFrames, split along the index.
    These Pandas DataFrames may live on disk for larger-than-memory computing on a single machine, or on many different machines in a cluster.
    One Dask DataFrame operation triggers many operations on the constituent Pandas DataFrames.
    See https://docs.dask.org/en/latest/dataframe.html""",
    loader=dataframe_loader,
    materializer=dataframe_materializer,
    type_check_fn=df_type_check,
)
