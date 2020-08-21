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
    String,
    TypeCheck,
    check,
    dagster_type_loader,
    dagster_type_materializer,
)
from dagster.config.field_utils import Selector

WriteCompressionTextOptions = Enum(
    "WriteCompressionText", [EnumValue("gzip"), EnumValue("bz2"), EnumValue("xz"),],
)

EngineParquetOptions = Enum(
    "EngineParquet", [EnumValue("auto"), EnumValue("fastparquet"), EnumValue("pyarrow"),],
)


def dict_without_keys(ddict, *keys):
    return {key: value for key, value in ddict.items() if key not in set(keys)}


@dagster_type_materializer(
    Selector(
        {
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
                            defaults to 'ascii' on Python 2 and 'utf-8' on Python 3.
                        """,
                    ),
                    "mode": Field(
                        String, is_required=False, description="Python write mode, default 'w'",
                    ),
                    "compression": Field(
                        WriteCompressionTextOptions,
                        is_required=False,
                        description="""
                            a string representing the compression to use in the output file,
                            allowed values are 'gzip', 'bz2', 'xz'.
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
                            {'auto', 'fastparquet', 'pyarrow'}, default 'auto' Parquet library to use.
                            If only one library is installed, it will use that one; if both, it will use 'fastparquet'.
                        """,
                    ),
                    "compression": Field(
                        Any,
                        is_required=False,
                        description="""
                        str or dict, optional Either a string like ``'snappy'``
                        or a dictionary mapping column names to compressors like ``{'name': 'gzip', 'values': 'snappy'}``.
                        The default is ``'default'``, which uses the default compression for whichever engine is selected.
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
                        description="Whether to write the special '_metadata' file.",
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
                        description="The scheduler to use, like 'threads' or 'processes'.",
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
                            Supports protocol specifications such as ``'s3://'``.
                        """,
                    ),
                    "encoding": Field(
                        String,
                        is_required=False,
                        description="default is 'utf-8', The text encoding to implement, e.g., 'utf-8'.",
                    ),
                    "errors": Field(
                        String,
                        is_required=False,
                        description="default is 'strict', how to respond to errors in the conversion (see ``str.encode()``).",
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
                        String, is_required=False, description="String like 'gzip' or 'xz'.",
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
                            {'fail', 'replace', 'append'}, default 'fail'"
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
                            {None, 'multi', callable}, default None
                            Controls the SQL insertion clause used:
                            * None : Uses standard SQL ``INSERT`` clause (one per row).
                            * 'multi': Pass multiple values in a single ``INSERT`` clause.
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
                            This can result in DB rows being in a different order than the source DataFrame's corresponding rows.
                            When false, load each block into the SQL DB in sequence.
                        """,
                    ),
                },
            ),
        },
    )
)
def dataframe_materializer(_context, config, dask_df):
    check.inst_param(dask_df, "dask_df", dd.DataFrame)
    file_type, file_options = list(config.items())[0]
    path = file_options.get("path")

    if file_type == "csv":
        dask_df.to_csv(path, **dict_without_keys(file_options, "path"))
    elif file_type == "parquet":
        dask_df.to_parquet(path, **dict_without_keys(file_options, "path"))
    elif file_type == "hdf":
        dask_df.to_hdf(path, **dict_without_keys(file_options, "path"))
    elif file_type == "json":
        dask_df.to_json(path, **dict_without_keys(file_options, "path"))
    elif file_type == "sql":
        dask_df.to_sql(**file_options)
    else:
        check.failed("Unsupported file_type {file_type}".format(file_type=file_type))

    return AssetMaterialization.file(path)


@dagster_type_loader(
    Selector(
        {
            "csv": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or list, Absolute or relative filepath(s).
                            Prefix with a protocol like `s3://` to read from alternative filesystems.
                            To read from multiple files you can pass a globstring or a list of paths,
                            with the caveat that they must all have the same protocol.
                        """,
                    ),
                    "blocksize": Field(
                        Any,
                        is_required=False,
                        description="""
                        str or int or None, Number of bytes by which to cut up larger files.
                        Default value is computed based on available physical memory and the number of cores, up to a maximum of 64MB.
                        Can be a number like 64000000` or a string like ``'64MB'. If None, a single block is used for each file.
                        """,
                    ),
                    "sample": Field(
                        Int,
                        is_required=False,
                        description="Number of bytes to use when determining dtypes.",
                    ),
                    "assume_missing": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If True, all integer columns that aren’t specified in `dtype` are assumed to contain missing values,
                            and are converted to floats. Default is False.
                        """,
                    ),
                    "storage_options": Field(
                        Permissive(),
                        is_required=False,
                        description="""
                            Extra options that make sense for a particular storage connection,
                            e.g. host, port, username, password, etc.
                        """,
                    ),
                    "include_path_column": Field(
                        Any,
                        is_required=False,
                        description="""
                            bool or str, Whether or not to include the path to each particular file.
                            If True a new column is added to the dataframe called path.
                            If str, sets new column name. Default is False.
                        """,
                    ),
                }
            ),
            "parquet": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or list, Source directory for data, or path(s) to individual parquet files.
                            Prefix with a protocol like s3:// to read from alternative filesystems.
                            To read from multiple files you can pass a globstring or a list of paths,
                            with the caveat that they must all have the same protocol.
                        """,
                    ),
                    "columns": Field(
                        Any,
                        is_required=False,
                        description="""
                            str or list or None (default), Field name(s) to read in as columns in the output.
                            By default all non-index fields will be read (as determined by the pandas parquet metadata, if present).
                            Provide a single field name instead of a list to read in the data as a Series.
                        """,
                    ),
                    "index": Field(
                        Any,
                        is_required=False,
                        description="""
                            list or False or None (default), Field name(s) to use as the output frame index.
                            By default will be inferred from the pandas parquet file metadata (if present).
                            Use False to read all fields as columns.
                        """,
                    ),
                    "categories": Field(
                        Any,
                        is_required=False,
                        description="""
                            list or dict or None, For any fields listed here,
                            if the parquet encoding is Dictionary, the column will be created with dtype category.
                            Use only if it is guaranteed that the column is encoded as dictionary in all row-groups.
                            If a list, assumes up to 2**16-1 labels; if a dict, specify the number of labels expected;
                            if None, will load categories automatically for data written by dask/fastparquet, not otherwise.
                        """,
                    ),
                    "storage_options": Field(
                        Permissive(),
                        is_required=False,
                        description="Key/value pairs to be passed on to the file-system backend, if any.",
                    ),
                    "engine": Field(
                        EngineParquetOptions,
                        is_required=False,
                        description="""
                            Parquet reader library to use.
                            If only one library is installed, it will use that one;
                            if both, it will use ‘fastparquet’.
                        """,
                    ),
                    "gather_statistics": Field(
                        Bool,
                        is_required=False,
                        description="""
                            default is None, Gather the statistics for each dataset partition.
                            By default, this will only be done if the _metadata file is available.
                            Otherwise, statistics will only be gathered if True,
                            because the footer of every file will be parsed (which is very slow on some systems).
                        """,
                    ),
                    "split_row_groups:": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If True (default) then output dataframe partitions will correspond
                            to parquet-file row-groups (when enough row-group metadata is available).
                            Otherwise, partitions correspond to distinct files.
                            Only the “pyarrow” engine currently supports this argument.
                        """,
                    ),
                    "chunksize": Field(
                        Any,
                        is_required=False,
                        description="""
                            int or string, The target task partition size.
                            If set, consecutive row-groups from the same file will be aggregated
                            into the same output partition until the aggregate size reaches this value.
                        """,
                    ),
                }
            ),
            "hdf": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or pathlib.Path or list,
                            File pattern (string), pathlib.Path, buffer to read from, or list of file paths.
                            Can contain wildcards.
                        """,
                    ),
                    "Key": Field(
                        Any,
                        is_required=True,
                        description="group identifier in the store. Can contain wildcards.",
                    ),
                    "start": Field(
                        Int,
                        is_required=False,
                        description="defaults to 0, row number to start at.",
                    ),
                    "stop": Field(
                        Int,
                        is_required=False,
                        description="defaults to None (the last row), row number to stop at.",
                    ),
                    "columns": Field(
                        list,
                        is_required=False,
                        description="A list of columns that if not None, will limit the return columns (default is None).",
                    ),
                    "chunksize": Field(
                        Any,
                        is_required=False,
                        description="Maximal number of rows per partition (default is 1000000).",
                    ),
                    "sorted_index": Field(
                        Bool,
                        is_required=False,
                        description="Option to specify whether or not the input hdf files have a sorted index (default is False).",
                    ),
                    "lock": Field(
                        Bool,
                        is_required=False,
                        description="Option to use a lock to prevent concurrency issues (default is True).",
                    ),
                    "mode": Field(
                        String,
                        is_required=False,
                        description="""
                            {‘a’, ‘r’, ‘r+’}, default ‘a’. Mode to use when opening file(s).
                            ‘r’ - Read-only; no data can be modified.
                            ‘a’ - Append; an existing file is opened for reading and writing, and if the file does not exist it is created.
                            ‘r+’ - It is similar to ‘a’, but the file must already exist.
                        """,
                    ),
                }
            ),
            "json": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or list, Location to read from.
                            If a string, can include a glob character to find a set of file names.
                            Supports protocol specifications such as 's3://'.
                        """,
                    ),
                    "encoding": Field(
                        String,
                        is_required=False,
                        description="The text encoding to implement, e.g., “utf-8”.",
                    ),
                    "errors": Field(
                        String,
                        is_required=False,
                        description="how to respond to errors in the conversion (see str.encode()).",
                    ),
                    "orient": Field(
                        String, is_required=False, description="The JSON string format."
                    ),
                    "storage_option": Field(
                        Permissive(),
                        is_required=False,
                        description="Passed to backend file-system implementation.",
                    ),
                    "blocksize": Field(
                        Int,
                        is_required=False,
                        description="""
                            default is None, If None, files are not blocked, and you get one partition per input file.
                            If int, which can only be used for line-delimited JSON files,
                            each partition will be approximately this size in bytes, to the nearest newline character.
                        """,
                    ),
                    "sample": Field(
                        Int,
                        is_required=False,
                        description="""
                            Number of bytes to pre-load,
                            to provide an empty dataframe structure to any blocks without data.
                            Only relevant is using blocksize.
                        """,
                    ),
                    "compression": Field(
                        String,
                        is_required=False,
                        description="default is None, String like ‘gzip’ or ‘xz’.",
                    ),
                }
            ),
            "sql_table": Permissive(
                {
                    "table": Field(
                        Any,
                        is_required=True,
                        description="str or sqlalchemy expression, Select columns from here.",
                    ),
                    "uri": Field(
                        String,
                        is_required=True,
                        description="Full sqlalchemy URI for the database connection.",
                    ),
                    "index_col": Field(
                        String,
                        is_required=True,
                        description="""
                        Column which becomes the index, and defines the partitioning.
                        Should be a indexed column in the SQL server, and any orderable type.
                        If the type is number or time, then partition boundaries can be inferred from npartitions or bytes_per_chunk;
                        otherwide must supply explicit divisions=.
                        index_col could be a function to return a value, e.g., sql.func.abs(sql.column('value')).label('abs(value)').
                        index_col=sql.func.abs(sql.column("value")).label("abs(value)"),
                        or index_col=cast(sql.column("id"),types.BigInteger).label("id") to convert the textfield id to BigInteger.
                        Note sql, cast, types methods comes frome sqlalchemy module.
                        Labeling columns created by functions or arithmetic operations is required
                        """,
                    ),
                    "divisions": Field(
                        Any,
                        is_required=False,
                        description="""
                            sequence, Values of the index column to split the table by.
                            If given, this will override npartitions and bytes_per_chunk.
                            The divisions are the value boundaries of the index column used to define the partitions.
                            For example, divisions=list('acegikmoqsuwz') could be used
                            to partition a string column lexographically into 12 partitions,
                            with the implicit assumption that each partition contains similar numbers of records.
                        """,
                    ),
                    "npartitions": Field(
                        Int,
                        is_required=False,
                        description="""
                            Number of partitions, if divisions is not given.
                            Will split the values of the index column linearly between limits, if given, or the column max/min.
                            The index column must be numeric or time for this to work.
                        """,
                    ),
                    "columns": Field(
                        Any,
                        is_required=False,
                        description="""
                            list of strings or None, Which columns to select;
                            if None, gets all; can include sqlalchemy functions,
                            e.g., sql.func.abs(sql.column('value')).label('abs(value)').
                            Labeling columns created by functions or arithmetic operations is recommended.
                        """,
                    ),
                    "bytes_per_chunk": Field(
                        Any,
                        is_required=False,
                        description="""
                            str or int, If both divisions and npartitions is None,
                            this is the target size of each partition, in bytes.
                        """,
                    ),
                    "head_rows": Field(
                        Int,
                        is_required=False,
                        description="How many rows to load for inferring the data-types, unless passing meta.",
                    ),
                    "schema": Field(
                        String,
                        is_required=False,
                        description="""
                            If using a table name, pass this to sqlalchemy to select
                            which DB schema to use within the URI connection.
                        """,
                    ),
                }
            ),
            "table": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or list, Absolute or relative filepath(s).
                            Prefix with a protocol like 's3://' to read from alternative filesystems.
                            To read from multiple files you can pass a globstring or a list of paths,
                            with the caveat that they must all have the same protocol.
                        """,
                    ),
                    "blocksize": Field(
                        Any,
                        is_required=False,
                        description="""
                            str or int or None, Number of bytes by which to cut up larger files.
                            Default value is computed based on available physical memory and the number of cores,
                            up to a maximum of 64MB. Can be a number like 64000000` or a string like ``'64MB'.
                            If None, a single block is used for each file.
                        """,
                    ),
                    "sample": Field(
                        Int,
                        is_required=False,
                        description="Number of bytes to use when determining dtypes.",
                    ),
                    "assume_missing": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If True, all integer columns that aren’t specified in dtype are assumed to contain missing values,
                            and are converted to floats. Default is False.
                        """,
                    ),
                    "storage_options": Field(
                        Permissive(),
                        is_required=False,
                        description="""
                            Extra options that make sense for a particular storage connection,
                            e.g. host, port, username, password, etc.
                        """,
                    ),
                    "include_path_column": Field(
                        Any,
                        is_required=False,
                        description="""
                            bool or str, Whether or not to include the path to each particular file.
                            If True a new column is added to the dataframe called path.
                            If str, sets new column name. Default is False.
                        """,
                    ),
                }
            ),
            "fwf": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or list, Absolute or relative filepath(s).
                            Prefix with a protocol like 's3://' to read from alternative filesystems.
                            To read from multiple files you can pass a globstring or a list of paths,
                            with the caveat that they must all have the same protocol.
                        """,
                    ),
                    "blocksize": Field(
                        Any,
                        is_required=False,
                        description="""
                            str or int or None, Number of bytes by which to cut up larger files.
                            Default value is computed based on available physical memory
                            and the number of cores up to a maximum of 64MB.
                            Can be a number like 64000000` or a string like ``'64MB'.
                            If None, a single block is used for each file.
                        """,
                    ),
                    "sample": Field(
                        Int,
                        is_required=False,
                        description="Number of bytes to use when determining dtypes.",
                    ),
                    "assume_missing": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If True, all integer columns that aren’t specified in dtype are assumed
                            to contain missing values, and are converted to floats.
                            Default is False.
                        """,
                    ),
                    "storage_options": Field(
                        Permissive(),
                        is_required=False,
                        description="""
                            Extra options that make sense for a particular storage connection,
                            e.g. host, port, username, password, etc.
                        """,
                    ),
                    "include_path_column": Field(
                        Any,
                        is_required=False,
                        description="""
                            bool or str, Whether or not to include the path to each particular file.
                            If True a new column is added to the dataframe called path.
                            If str, sets new column name. Default is False.
                        """,
                    ),
                }
            ),
            "orc": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            str or list, Location of file(s),
                            which can be a full URL with protocol specifier,
                            and may include glob character if a single string.
                        """,
                    ),
                    "columns": Field(
                        list, is_required=False, description="Columns to load. If None, loads all.",
                    ),
                    "storage_options": Field(
                        Permissive(),
                        is_required=False,
                        description="Further parameters to pass to the bytes backend.",
                    ),
                }
            ),
        },
    )
)
def dataframe_loader(_context, config):
    file_type, file_options = list(config.items())[0]
    path = file_options.get("path")

    if file_type == "csv":
        return dd.read_csv(path, **dict_without_keys(file_options, "path"))
    elif file_type == "parquet":
        return dd.read_parquet(path, **dict_without_keys(file_options, "path"))
    elif file_type == "hdf":
        return dd.read_hdf(path, **dict_without_keys(file_options, "path"))
    elif file_type == "json":
        return dd.read_json(path, **dict_without_keys(file_options, "path"))
    elif file_type == "sql_table":
        return dd.read_sql_table(**file_options)
    elif file_type == "table":
        return dd.read_table(path, **dict_without_keys(file_options, "path"))
    elif file_type == "fwf":
        return dd.read_fwf(path, **dict_without_keys(file_options, "path"))
    elif file_type == "orc":
        return dd.read_orc(path, **dict_without_keys(file_options, "path"))
    else:
        raise DagsterInvariantViolationError(
            "Unsupported file_type {file_type}".format(file_type=file_type)
        )


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
