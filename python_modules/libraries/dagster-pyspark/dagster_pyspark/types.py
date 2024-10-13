from dagster import (
    Any,
    Bool,
    DagsterInvariantViolationError,
    Enum,
    EnumValue,
    Field,
    Float,
    Int,
    Permissive,
    PythonObjectDagsterType,
    String,
    dagster_type_loader,
)
from dagster._config import Selector
from dagster._utils import dict_without_keys
from pyspark.sql import DataFrame as NativeSparkDataFrame

WriteModeOptions = Enum(
    "WriteMode",
    [
        EnumValue(
            "append",
            description="Append contents of this :class:`DataFrame` to existing data.",
        ),
        EnumValue("overwrite", description="Overwrite existing data."),
        EnumValue(
            "ignore",
            description="Silently ignore this operation if data already exists.",
        ),
        EnumValue(
            "error",
            description="(default case): Throw an exception if data already exists.",
        ),
        EnumValue(
            "errorifexists",
            description="(default case): Throw an exception if data already exists.",
        ),
    ],
)


WriteCompressionTextOptions = Enum(
    "WriteCompressionText",
    [
        EnumValue("none"),
        EnumValue("bzip2"),
        EnumValue("gzip"),
        EnumValue("lz4"),
        EnumValue("snappy"),
        EnumValue("deflate"),
    ],
)


WriteCompressionOrcOptions = Enum(
    "WriteCompressionOrc",
    [
        EnumValue("none"),
        EnumValue("snappy"),
        EnumValue("zlib"),
        EnumValue("lzo"),
    ],
)


WriteCompressionParquetOptions = Enum(
    "WriteCompressionParquet",
    [
        EnumValue("none"),
        EnumValue("uncompressed"),
        EnumValue("snappy"),
        EnumValue("gzip"),
        EnumValue("lzo"),
        EnumValue("brotli"),
        EnumValue("lz4"),
        EnumValue("zstd"),
    ],
)


@dagster_type_loader(
    config_schema=Selector(
        {
            "csv": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="""
                            string, or list of strings, for input path(s),
                            or RDD of Strings storing CSV rows.
                        """,
                    ),
                    "schema": Field(
                        Any,
                        is_required=False,
                        description="""
                            an optional :class:`pyspark.sql.types.StructType` for the input schema
                            or a DDL-formatted string (For example ``col0 INT, col1 DOUBLE``).
                        """,
                    ),
                    "sep": Field(
                        String,
                        is_required=False,
                        description="""
                            sets a separator (one or more characters) for each field and value.
                            If None is set, it uses the default value, ``,``.
                        """,
                    ),
                    "encoding": Field(
                        String,
                        is_required=False,
                        description="""
                            decodes the CSV files by the given encoding type.
                            If None is set, it uses the default value, ``UTF-8``.
                        """,
                    ),
                    "quote": Field(
                        String,
                        is_required=False,
                        description="""
                            sets a single character used for escaping quoted values
                            where the separator can be part of the value.
                            If None is set, it uses the default value, ``"``.
                            If you would like to turn off quotations, you need to set an empty string.
                        """,
                    ),
                    "escape": Field(
                        String,
                        is_required=False,
                        description=r"""
                            sets a single character used for escaping quotes inside an already quoted value.
                            If None is set, it uses the default value, ``\``.
                        """,
                    ),
                    "comment": Field(
                        String,
                        is_required=False,
                        description="""
                            sets a single character used for skipping lines beginning with this character.
                            By default (None), it is disabled.
                        """,
                    ),
                    "header": Field(
                        Bool,
                        is_required=False,
                        description="""
                            uses the first line as names of columns.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "inferSchema": Field(
                        Bool,
                        is_required=False,
                        description="""
                            infers the input schema automatically from data.
                            It requires one extra pass over the data.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "enforceSchema": Field(
                        Bool,
                        is_required=False,
                        description="""
                            If it is set to ``true``, the specified or inferred schema will be forcibly applied to datasource files,
                            and headers in CSV files will be ignored.
                            If the option is set to ``false``, the schema will be validated against all headers in CSV files
                            or the first header in RDD if the ``header`` option is set to ``true``.
                            If None is set, ``true`` is used by default.
                        """,
                    ),
                    "ignoreLeadingWhiteSpace": Field(
                        Bool,
                        is_required=False,
                        description="""
                            A flag indicating whether or not leading whitespaces from values being read should be skipped.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "ignoreTrailingWhiteSpace": Field(
                        Bool,
                        is_required=False,
                        description="""
                            A flag indicating whether or not trailing whitespaces from values being read should be skipped.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "nullValue": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string representation of a null value.
                            If None is set, it uses the default value, empty string.
                        """,
                    ),
                    "nanValue": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string representation of a non-number value.
                            If None is set, it uses the default value, ``NaN``.
                        """,
                    ),
                    "positiveInf": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string representation of a positive infinity value.
                            If None is set, it uses the default value, ``Inf``.
                        """,
                    ),
                    "negativeInf": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string representation of a negative infinity value.
                            If None is set, it uses the default value, ``Inf``.
                        """,
                    ),
                    "dateFormat": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string that indicates a date format.
                            Custom date formats follow the formats at `datetime pattern`_.
                            This applies to date type.
                            If None is set, it uses the default value, ``yyyy-MM-dd``.
                        """,
                    ),
                    "timestampFormat": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string that indicates a timestamp format.
                            Custom date formats follow the formats at `datetime pattern`_.
                            This applies to timestamp type.
                            If None is set, it uses the default value, ``yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]``.
                        """,
                    ),
                    "maxColumns": Field(
                        Int,
                        is_required=False,
                        description="""
                            defines a hard limit of how many columns a record can have.
                            If None is set, it uses the default value, ``20480``.
                        """,
                    ),
                    "maxCharsPerColumn": Field(
                        Int,
                        is_required=False,
                        description="""
                            defines the maximum number of characters allowed for any given value being read.
                            If None is set, it uses the default value, ``-1`` meaning unlimited length.
                        """,
                    ),
                    "mode": Field(
                        String,
                        is_required=False,
                        description="""
                            allows a mode for dealing with corrupt records during parsing.
                            If None is set, it uses the default value, ``PERMISSIVE``.
                        """,
                    ),
                    "columnNameOfCorruptRecord": Field(
                        String,
                        is_required=False,
                        description="""
                            allows renaming the new field having malformed string created by ``PERMISSIVE`` mode.
                            This overrides ``spark.sql.columnNameOfCorruptRecord``.
                            If None is set, it uses the value specified in ``spark.sql.columnNameOfCorruptRecord``.
                        """,
                    ),
                    "multiLine": Field(
                        Bool,
                        is_required=False,
                        description="""
                            parse records, which may span multiple lines.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "charToEscapeQuoteEscaping": Field(
                        String,
                        is_required=False,
                        description="""
                            sets a single character used for escaping the escape for the quote character.
                            If None is set, the default value is escape character
                            when escape and quote characters are different, ``\0`` otherwise.
                        """,
                    ),
                    "samplingRatio": Field(
                        Float,
                        is_required=False,
                        description="""
                            defines fraction of rows used for schema inferring.
                            If None is set, it uses the default value, ``1.0``.
                        """,
                    ),
                    "emptyValue": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string representation of an empty value.
                            If None is set, it uses the default value, empty string.
                        """,
                    ),
                    "locale": Field(
                        String,
                        is_required=False,
                        description="""
                            sets a locale as language tag in IETF BCP 47 format.
                            If None is set, it uses the default value, ``en-US``.
                            For instance, ``locale`` is used while parsing dates and timestamps.
                        """,
                    ),
                    "lineSep": Field(
                        String,
                        is_required=False,
                        description="""
                            defines the line separator that should be used for parsing.
                            If None is set, it covers all ``\\r``, ``\\r\\n`` and ``\\n``.
                            Maximum length is 1 character.
                        """,
                    ),
                    "pathGlobFilter": Field(
                        String,
                        is_required=False,
                        description="""
                            an optional glob pattern to only include files with paths matching the pattern.
                            The syntax follows `org.apache.hadoop.fs.GlobFilter`.
                            It does not change the behavior of `partition discovery`_.
                        """,
                    ),
                    "recursiveFileLookup": Field(
                        Bool,
                        is_required=False,
                        description="""
                            recursively scan a directory for files.
                            Using this option disables `partition discovery`_..
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
                            string, or list of strings, for input path(s).
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
                            string represents path to the JSON dataset, or a list of paths,
                            or RDD of Strings storing JSON objects.
                        """,
                    ),
                    "schema": Field(
                        Any,
                        is_required=False,
                        description="""
                            an optional :class:`pyspark.sql.types.StructType` for the input schema
                            or a DDL-formatted string (For example ``col0 INT, col1 DOUBLE``).
                        """,
                    ),
                    "primitivesAsString": Field(
                        Bool,
                        is_required=False,
                        description="""
                            infers all primitive values as a string type.
                            If None is set, it uses the default value, ``false``..
                        """,
                    ),
                    "prefersDecimal": Field(
                        Bool,
                        is_required=False,
                        description="""
                            infers all floating-point values as a decimal type.
                            If the values do not fit in decimal, then it infers them as doubles.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "allowComments": Field(
                        Bool,
                        is_required=False,
                        description="""
                            ignores Java/C++ style comment in JSON records.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "allowUnquotedFieldNames": Field(
                        String,
                        is_required=False,
                        description="""
                            allows unquoted JSON field names.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "allowSingleQuotes": Field(
                        Bool,
                        is_required=False,
                        description="""
                            allows single quotes in addition to double quotes.
                            If None is set, it uses the default value, ``true``.
                        """,
                    ),
                    "allowNumericLeadingZero": Field(
                        Bool,
                        is_required=False,
                        description="""
                            allows leading zeros in numbers (e.g. 00012).
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "allowBackslashEscapingAnyCharacter": Field(
                        Bool,
                        is_required=False,
                        description="""
                            allows accepting quoting of all character using backslash quoting mechanism.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "mode": Field(
                        String,
                        is_required=False,
                        description="""
                            allows a mode for dealing with corrupt records during parsing.
                            If None is set, it uses the default value, ``PERMISSIVE``.
                        """,
                    ),
                    "columnNameOfCorruptRecord": Field(
                        String,
                        is_required=False,
                        description="""
                            allows renaming the new field having malformed string created by ``PERMISSIVE`` mode.
                            This overrides ``spark.sql.columnNameOfCorruptRecord``.
                            If None is set, it uses the value specified in ``spark.sql.columnNameOfCorruptRecord``.
                        """,
                    ),
                    "dateFormat": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string that indicates a date format.
                            Custom date formats follow the formats at `datetime pattern`_.
                            This applies to date type.
                            If None is set, it uses the default value, ``yyyy-MM-dd``.
                        """,
                    ),
                    "timestampFormat": Field(
                        String,
                        is_required=False,
                        description="""
                            sets the string that indicates a timestamp format.
                            Custom date formats follow the formats at `datetime pattern`_.
                            This applies to timestamp type.
                            If None is set, it uses the default value, ``yyyy-MM-dd'T'HH:mm:ss[.SSS][XXX]``.
                        """,
                    ),
                    "multiLine": Field(
                        Bool,
                        is_required=False,
                        description="""
                            parse one record, which may span multiple lines, per file.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "allowUnquotedControlChars": Field(
                        Bool,
                        is_required=False,
                        description="""
                            allows JSON Strings to contain unquoted control
                            characters (ASCII characters with value less than 32,
                            including tab and line feed characters) or not.
                        """,
                    ),
                    "encoding": Field(
                        String,
                        is_required=False,
                        description="""
                            allows to forcibly set one of standard basic or extended encoding for the JSON files.
                            For example UTF-16BE, UTF-32LE.
                            If None is set, the encoding of input JSON will be detected automatically
                            when the multiLine option is set to ``true``.
                        """,
                    ),
                    "lineSep": Field(
                        String,
                        is_required=False,
                        description="""
                            defines the line separator that should be used for parsing.
                            If None is set, it covers all ``\\r``, ``\\r\\n`` and ``\\n``.
                            Maximum length is 1 character.
                        """,
                    ),
                    "samplingRatio": Field(
                        Float,
                        is_required=False,
                        description="""
                            defines fraction of input JSON objects used for schema inferring.
                            If None is set, it uses the default value, ``1.0``.
                        """,
                    ),
                    "dropFieldIfAllNull": Field(
                        Bool,
                        is_required=False,
                        description="""
                            whether to ignore column of all null values or empty array/struct during schema inference.
                            If None is set, it uses the default value, ``false``.
                        """,
                    ),
                    "locale": Field(
                        String,
                        is_required=False,
                        description="""
                            sets a locale as language tag in IETF BCP 47 format.
                            If None is set, it uses the default value, ``en-US``.
                            For instance, ``locale`` is used while parsing dates and timestamps.
                        """,
                    ),
                    "pathGlobFilter": Field(
                        String,
                        is_required=False,
                        description="""
                            an optional glob pattern to only include files with paths matching the pattern.
                            The syntax follows `org.apache.hadoop.fs.GlobFilter`.
                            It does not change the behavior of `partition discovery`_.
                        """,
                    ),
                    "recursiveFileLookup": Field(
                        Bool,
                        is_required=False,
                        description="""
                            recursively scan a directory for files.
                            Using this option disables `partition discovery`_..
                        """,
                    ),
                }
            ),
            "jdbc": Permissive(
                {
                    "url": Field(
                        String,
                        is_required=True,
                        description="a JDBC URL of the form ``jdbc:subprotocol:subname``.",
                    ),
                    "table": Field(
                        String,
                        is_required=True,
                        description="the name of the table.",
                    ),
                    "column": Field(
                        String,
                        is_required=False,
                        description="""
                            the name of a column of numeric, date, or timestamp type
                            that will be used for partitioning;
                            if this parameter is specified, then ``numPartitions``, ``lowerBound``
                            (inclusive), and ``upperBound`` (exclusive) will form partition strides
                            for generated WHERE clause expressions used to split the column
                            ``column`` evenly.
                        """,
                    ),
                    "lowerBound": Field(
                        Int,
                        is_required=False,
                        description=(
                            "the minimum value of ``column`` used to decide partition stride."
                        ),
                    ),
                    "upperBound": Field(
                        Int,
                        is_required=False,
                        description=(
                            "the maximum value of ``column`` used to decide partition stride."
                        ),
                    ),
                    "numPartitions": Field(
                        Int,
                        is_required=False,
                        description="the number of partitions",
                    ),
                    "predicates": Field(
                        list,
                        is_required=False,
                        description="""
                            a list of expressions suitable for inclusion in WHERE clauses;
                            each one defines one partition of the :class:`DataFrame`
                        """,
                    ),
                    "properties": Field(
                        Permissive(),
                        is_required=False,
                        description="""
                            a dictionary of JDBC database connection arguments. Normally at
                            least properties "user" and "password" with their corresponding values.
                            For example { 'user' : 'SYSTEM', 'password' : 'mypassword' }
                        """,
                    ),
                }
            ),
            "orc": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="string, or list of strings, for input path(s).",
                    ),
                }
            ),
            "table": Permissive(
                {
                    "tableName": Field(
                        String,
                        is_required=True,
                        description="string, name of the table.",
                    ),
                }
            ),
            "text": Permissive(
                {
                    "path": Field(
                        Any,
                        is_required=True,
                        description="string, or list of strings, for input path(s).",
                    ),
                    "wholetext": Field(
                        Bool,
                        is_required=False,
                        description="if true, read each file from input path(s) as a single row.",
                    ),
                    "lineSep": Field(
                        String,
                        is_required=False,
                        description="""
                            defines the line separator that should be used for parsing.
                            If None is set, it covers all ``\\r``, ``\\r\\n`` and ``\\n``.
                        """,
                    ),
                    "pathGlobFilter": Field(
                        String,
                        is_required=False,
                        description="""
                            an optional glob pattern to only include files with paths matching the pattern.
                            The syntax follows `org.apache.hadoop.fs.GlobFilter`.
                            It does not change the behavior of `partition discovery`_.
                        """,
                    ),
                    "recursiveFileLookup": Field(
                        Bool,
                        is_required=False,
                        description="""
                            recursively scan a directory for files.
                            Using this option disables `partition discovery`_..
                        """,
                    ),
                }
            ),
            "other": Permissive(),
        },
    ),
    required_resource_keys={"pyspark"},
)
def dataframe_loader(_context, config):
    spark_read = _context.resources.pyspark.spark_session.read
    file_type, file_options = next(iter(config.items()))
    path = file_options.get("path")

    if file_type == "csv":
        return spark_read.csv(path, **dict_without_keys(file_options, "path"))
    elif file_type == "parquet":
        return spark_read.parquet(path, **dict_without_keys(file_options, "path"))
    elif file_type == "json":
        return spark_read.json(path, **dict_without_keys(file_options, "path"))
    elif file_type == "jdbc":
        return spark_read.jdbc(**file_options)
    elif file_type == "orc":
        return spark_read.orc(path, **dict_without_keys(file_options, "path"))
    elif file_type == "table":
        return spark_read.table(**file_options)
    elif file_type == "text":
        return spark_read.text(path, **dict_without_keys(file_options, "path"))
    elif file_type == "other":
        return spark_read.load(**file_options)
    else:
        raise DagsterInvariantViolationError(f"Unsupported file_type {file_type}")


DataFrame = PythonObjectDagsterType(
    python_type=NativeSparkDataFrame,
    name="PySparkDataFrame",
    description="A PySpark data frame.",
    loader=dataframe_loader,
)
