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
    Float,
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

WriteCompressionTextOptions = Enum(
    "WriteCompressionText", [EnumValue("gzip"), EnumValue("bz2"), EnumValue("xz"),],
)

EngineParquetOptions = Enum(
    "EngineParquet", [EnumValue("auto"), EnumValue("fastparquet"), EnumValue("pyarrow"),],
)


def dict_without_keys(ddict, *keys):
    return {key: value for key, value in ddict.items() if key not in set(keys)}


DataFrameReadTypes = {
    "csv": {
        "function": dd.read_csv,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "blocksize": (Any, False, "Number of bytes by which to cut up larger files."),
            "sample": (Int, False, "Number of bytes to use when determining dtypes."),
            "assume_missing": (Bool, False, "If True, all integer columns that aren’t specified in `dtype` are assumed to contain missing values, and are converted to floats."),
            "storage_options": (Permissive(), False, "Extra options that make sense for a particular storage connection."),
            "include_path_column": (Any, False, "Whether or not to include the path to each particular file."),
        },
    },
    "parquet": {
        "function": dd.read_parquet,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "columns": (Any, False, "Field name(s) to read in as columns in the output."),
            "index": (Any, False, "Field name(s) to use as the output frame index."),
            "categories": (Any, False, "For any fields listed here, if the parquet encoding is Dictionary, the column will be created with dtype category."),
            "storage_options": (Permissive(), False, "Key/value pairs to be passed on to the file-system backend, if any."),
            "engine": (EngineParquetOptions, False, "Parquet reader library to use."),
            "gather_statistics": (Bool, False, "Gather the statistics for each dataset partition."),
            "split_row_groups": (Bool, False, "If True (default) then output dataframe partitions will correspond to parquet-file row-groups."),
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
            "sorted_index": (Bool, False, "Option to specify whether or not the input hdf files have a sorted index."),
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
            "storage_options": (Permissive(), False, "Passed to backend file-system implementation."),
            "blocksize": (Int, False, "Each partition will be approximately this size in bytes."),
            "sample": (Int, False, "Number of bytes to pre-load, to provide an empty dataframe structure to any blocks without data."),
            "compression": (String, False, "String like ‘gzip’ or ‘xz’."),
        },
    },
    "sql_table": {
        "function": dd.read_sql_table,
        "is_path_based": False,
        "options": {
            "table": (Any, True, "Select columns from here."),
            "uri": (String, True, "Full sqlalchemy URI for the database connection."),
            "index_col": (String, True, "Column which becomes the index, and defines the partitioning."),
            "divisions": (Any, False, "Values of the index column to split the table by."),
            "npartitions": (Int, False, "Number of partitions, if divisions is not given."),
            "columns": (Any, False, "Which columns to select."),
            "bytes_per_chunk": (Any, False, "The target size of each partition, in bytes."),
            "head_rows": (Int, False, "How many rows to load for inferring the data-types, unless passing meta."),
            "schema": (String, False, "If using a table name, pass this to sqlalchemy to select which DB schema to use within the URI connection."),
        },
    },
    "table": {
        "function": dd.read_table,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "blocksize": (Any, False, "Number of bytes by which to cut up larger files."),
            "sample": (Int, False, "Number of bytes to use when determining dtypes."),
            "assume_missing": (Bool, False, "If True, all integer columns that aren’t specified in dtype are assumed to contain missing values, and are converted to floats."),
            "storage_options": (Permissive(), False, "Extra options that make sense for a particular storage connection."),
            "include_path_column": (Any, False, "Whether or not to include the path to each particular file."),
        },
    },
    "fwf": {
        "function": dd.read_fwf,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "blocksize": (Any, False, "Number of bytes by which to cut up larger files."),
            "sample": (Int, False, "Number of bytes to use when determining dtypes."),
            "assume_missing": (Bool, False, "If True, all integer columns that aren’t specified in dtype are assumed to contain missing values, and are converted to floats."),
            "storage_options": (Permissive(), False, "Extra options that make sense for a particular storage connection."),
            "include_path_column": (Any, False, "Whether or not to include the path to each particular file."),
        }
    },
    "orc": {
        "function": dd.read_orc,
        "is_path_based": True,
        "options": {
            "path": (Any, True, "Absolute or relative filepath(s)."),
            "columns": (Any, False, "Columns to load."),
            "storage_options": (Permissive(), False, "Further parameters to pass to the bytes backend."),
        }
    }
}


def _dataframe_loader_config():
    read_fields = Selector({
        read_from: {
            option_name: Field(option_args[0], is_required=option_args[1], description=option_args[2])
            for option_name, option_args in read_opts["options"].items()
        }
        for read_from, read_opts in DataFrameReadTypes.items()
    })

    return Shape({
        "read": read_fields
    })


@dagster_type_loader(_dataframe_loader_config())
def dataframe_loader(_context, config):
    read_type, read_options = next(iter(config["read"].items()))
    path = read_options.get("path")

    if read_type == "csv":
        return dd.read_csv(path, **dict_without_keys(read_options, "path"))
    elif read_type == "parquet":
        return dd.read_parquet(path, **dict_without_keys(read_options, "path"))
    elif read_type == "hdf":
        return dd.read_hdf(path, **dict_without_keys(read_options, "path"))
    elif read_type == "json":
        return dd.read_json(path, **dict_without_keys(read_options, "path"))
    elif read_type == "sql_table":
        return dd.read_sql_table(**read_options)
    elif read_type == "table":
        return dd.read_table(path, **dict_without_keys(read_options, "path"))
    elif read_type == "fwf":
        return dd.read_fwf(path, **dict_without_keys(read_options, "path"))
    elif read_type == "orc":
        return dd.read_orc(path, **dict_without_keys(read_options, "path"))
    else:
        raise DagsterInvariantViolationError(
            "Unsupported read_type {read_type}".format(read_type=read_type)
        )


@dagster_type_materializer(
    Shape({
        "to": {
            "csv": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="str or list, Path glob indicating the naming scheme for the output files",
                    ),
                    "single_file": Field(
                        Bool,
                        is_required=False,
                        description="""
                            Whether to save everything into a single CSV file.
                            Under the single file mode, each partition is appended at the end of the specified CSV file.
                            Note that not all filesystems support the append mode and thus the single file mode,
                            especially on cloud storage systems such as S3 or GCS.
                            A warning will be issued when writing to a file that is not backed by a local filesystem.
                        """,
                    ),
                    "encoding": Field(
                        String,
                        is_required=False,
                        description="""
                            A string representing the encoding to use in the output file,
                            defaults to "ascii" on Python 2 and "utf-8" on Python 3.
                        """,
                    ),
                    "mode": Field(
                        String, is_required=False, description="Python write mode, default "w"",
                    ),
                    "compression": Field(
                        WriteCompressionTextOptions,
                        is_required=False,
                        description="""
                            a string representing the compression to use in the output file,
                            allowed values are "gzip", "bz2", "xz".
                        """,
                    ),
                    "compute": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If true, immediately executes.
                            If False, returns a set of delayed objects, which can be computed at a later time.
                        """,
                    ),
                    "storage_options": Field(
                        Permissive(),
                        is_required=False,
                        description="Parameters passed on to the backend filesystem class.",
                    ),
                    "header_first_partition_only": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If set to `True`, only write the header row in the first output file.
                            By default, headers are written to all partitions
                            under the multiple file mode (`single_file` is `False`)
                            and written only once under the single file mode (`single_file` is `True`).
                            It must not be `False` under the single file mode.
                        """,
                    ),
                    "compute_kwargs": Field(
                        Permissive(),
                        is_required=False,
                        description="Options to be passed in to the compute method",
                    ),
                }
            ),
            "parquet": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or pathlib.Path, Destination directory for data.
                            Prepend with protocol like ``s3://`` or ``hdfs://`` for remote data.
                        """,
                    ),
                    "engine": Field(
                        EngineParquetOptions,
                        is_required=False,
                        description="""
                            {"auto", "fastparquet", "pyarrow"}, default "auto" Parquet library to use.
                            If only one library is installed, it will use that one; if both, it will use "fastparquet".
                        """,
                    ),
                    "compression": Field(
                        Any,
                        is_required=False,
                        description="""
                        str or dict, optional Either a string like ``"snappy"``
                        or a dictionary mapping column names to compressors like ``{"name": "gzip", "values": "snappy"}``.
                        The default is ``"default"``, which uses the default compression for whichever engine is selected.
                        """,
                    ),
                    "write_index": Field(
                        Bool,
                        is_required=False,
                        description="Whether or not to write the index. Defaults to True.",
                    ),
                    "append": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If False (default), construct data-set from scratch.
                            If True, add new row-group(s) to an existing data-set.
                            In the latter case, the data-set must exist, and the schema must match the input data.
                        """,
                    ),
                    "ignore_divisions": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If False (default) raises error when previous divisions overlap with the new appended divisions.
                            Ignored if append=False.
                        """,
                    ),
                    "partition_on": Field(
                        list,
                        is_required=False,
                        description="""
                            Construct directory-based partitioning by splitting on these fields values.
                            Each dask partition will result in one or more datafiles, there will be no global groupby.
                        """,
                    ),
                    "storage_options": Field(
                        Permissive(),
                        is_required=False,
                        description="Key/value pairs to be passed on to the file-system backend, if any.",
                    ),
                    "write_metadata_file": Field(
                        Bool,
                        is_required=False,
                        description="Whether to write the special "_metadata" file.",
                    ),
                    "compute": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If True (default) then the result is computed immediately.
                            If False then a ``dask.delayed`` object is returned for future computation.
                        """,
                    ),
                    "compute_kwargs": Field(
                        Permissive(),
                        is_required=False,
                        description="Options to be passed in to the compute method.",
                    ),
                }
            ),
            "hdf": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or pathlib.Path, Path to a target filename.
                            Supports strings, ``pathlib.Path``, or any object implementing the ``__fspath__`` protocol.
                            May contain a ``*`` to denote many filenames.
                        """,
                    ),
                    "key": Field(
                        String,
                        is_required=True,
                        description="""
                            Datapath within the files.
                            May contain a ``*`` to denote many locations.
                        """,
                    ),
                    "compute": Field(
                        Bool,
                        is_required=False,
                        description="""
                            Whether or not to execute immediately.
                            If False then this returns a ``dask.Delayed`` value.
                        """,
                    ),
                    "scheduler": Field(
                        String,
                        is_required=False,
                        description="The scheduler to use, like "threads" or "processes".",
                    ),
                }
            ),
            "json": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or list, Location to write to.
                            If a string, and there are more than one partitions in df,
                            should include a glob character to expand into a set of file names,
                            or provide a ``name_function=`` parameter.
                            Supports protocol specifications such as ``"s3://"``.
                        """,
                    ),
                    "encoding": Field(
                        String,
                        is_required=False,
                        description="default is "utf-8", The text encoding to implement, e.g., "utf-8".",
                    ),
                    "errors": Field(
                        String,
                        is_required=False,
                        description="default is "strict", how to respond to errors in the conversion (see ``str.encode()``).",
                    ),
                    "storage_options": Field(
                        Permissive(),
                        is_required=False,
                        description="Passed to backend file-system implementation",
                    ),
                    "compute": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If true, immediately executes.
                            If False, returns a set of delayed objects, which can be computed at a later time.
                        """,
                    ),
                    "compute_kwargs": Field(
                        Permissive(),
                        is_required=False,
                        description="Options to be passed in to the compute method",
                    ),
                    "compression": Field(
                        String, is_required=False, description="String like "gzip" or "xz".",
                    ),
                },
            ),
            "sql": Permissive(
                {
                    "name": Field(String, is_required=True, description="Name of SQL table",),
                    "uri": Field(
                        String,
                        is_required=True,
                        description="Full sqlalchemy URI for the database connection",
                    ),
                    "schema": Field(
                        String,
                        is_required=False,
                        description="Specify the schema (if database flavor supports this). If None, use default schema.",
                    ),
                    "if_exists": Field(
                        String,
                        is_required=False,
                        description="""
                            {"fail", "replace", "append"}, default "fail""
                            How to behave if the table already exists.
                            * fail: Raise a ValueError.
                            * replace: Drop the table before inserting new values.
                            * append: Insert new values to the existing table.
                        """,
                    ),
                    "index": Field(
                        Bool,
                        is_required=False,
                        description="""
                            default is True, Write DataFrame index as a column.
                            Uses `index_label` as the column name in the table.
                        """,
                    ),
                    "index_label": Field(
                        Any,
                        is_required=False,
                        description="""
                            str or sequence, default None Column label for index column(s).
                            If None is given (default) and `index` is True, then the index names are used.
                            A sequence should be given if the DataFrame uses MultiIndex.
                        """,
                    ),
                    "chunksize": Field(
                        Int,
                        is_required=False,
                        description="""
                            Specify the number of rows in each batch to be written at a time.
                            By default, all rows will be written at once.
                        """,
                    ),
                    "dtype": Field(
                        Any,
                        is_required=False,
                        description="""
                            dict or scalar, Specifying the datatype for columns.
                            If a dictionary is used, the keys should be the column names
                            and the values should be the SQLAlchemy types or strings for the sqlite3 legacy mode.
                            If a scalar is provided, it will be applied to all columns.
                        """,
                    ),
                    "method": Field(
                        String,
                        is_required=False,
                        description="""
                            {None, "multi", callable}, default None
                            Controls the SQL insertion clause used:
                            * None : Uses standard SQL ``INSERT`` clause (one per row).
                            * "multi": Pass multiple values in a single ``INSERT`` clause.
                            * callable with signature ``(pd_table, conn, keys, data_iter)``.
                            Details and a sample callable implementation can be found in the
                            section :ref:`insert method <io.sql.method>`.
                        """,
                    ),
                    "compute": Field(
                        Bool,
                        is_required=False,
                        description="""
                            default is True, When true, call dask.compute and perform the load into SQL;
                            otherwise, return a Dask object (or array of per-block objects when parallel=True).
                        """,
                    ),
                    "parallel": Field(
                        Bool,
                        is_required=False,
                        description="""
                            default is False, When true, have each block append itself to the DB table concurrently.
                            This can result in DB rows being in a different order than the source DataFrame"s corresponding rows.
                            When false, load each block into the SQL DB in sequence.
                        """,
                    ),
                },
            ),
        },
    })
)
def dataframe_materializer(_context, config, dask_df):
    check.inst_param(dask_df, "dask_df", dd.DataFrame)

    for to_type, to_options in config["to"].items():
        path = to_options.get("path")

        if to_type == "csv":
            dask_df.to_csv(path, **dict_without_keys(to_options, "path"))
        elif to_type == "parquet":
            dask_df.to_parquet(path, **dict_without_keys(to_options, "path"))
        elif to_type == "hdf":
            dask_df.to_hdf(path, **dict_without_keys(to_options, "path"))
        elif to_type == "json":
            dask_df.to_json(path, **dict_without_keys(to_options, "path"))
        elif to_type == "sql":
            dask_df.to_sql(**to_options)
        else:
            check.failed("Unsupported to_type {to_type}".format(to_type=to_type))

        yield AssetMaterialization.file(path)


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
