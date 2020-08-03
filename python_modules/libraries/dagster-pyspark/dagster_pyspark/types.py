import os

from pyspark.sql import DataFrame as NativeSparkDataFrame

from dagster import (
    AssetMaterialization,
    Bool,
    Enum,
    EnumValue,
    Field,
    Permissive,
    PythonObjectDagsterType,
    String,
    check,
    dagster_type_materializer,
)
from dagster.config.field_utils import Selector
from dagster.core.storage.system_storage import fs_intermediate_storage, fs_system_storage
from dagster.core.storage.type_storage import TypeStoragePlugin

WriteModeOptions = Enum(
    'WriteMode',
    [
        EnumValue(
            'append', description="Append contents of this :class:`DataFrame` to existing data."
        ),
        EnumValue('overwrite', description="Overwrite existing data."),
        EnumValue('ignore', description="Silently ignore this operation if data already exists."),
        EnumValue(
            'error', description="(default case): Throw an exception if data already exists."
        ),
        EnumValue(
            'errorifexists',
            description="(default case): Throw an exception if data already exists.",
        ),
    ],
)


WriteCompressionTextOptions = Enum(
    'WriteCompressionText',
    [
        EnumValue('none'),
        EnumValue('bzip2'),
        EnumValue('gzip'),
        EnumValue('lz4'),
        EnumValue('snappy'),
        EnumValue('deflate'),
    ],
)


WriteCompressionOrcOptions = Enum(
    'WriteCompressionOrc',
    [EnumValue('none'), EnumValue('snappy'), EnumValue('zlib'), EnumValue('lzo'),],
)


WriteCompressionParquetOptions = Enum(
    'WriteCompressionParquet',
    [
        EnumValue('none'),
        EnumValue('uncompressed'),
        EnumValue('snappy'),
        EnumValue('gzip'),
        EnumValue('lzo'),
        EnumValue('brotli'),
        EnumValue('lz4'),
        EnumValue('zstd'),
    ],
)


@dagster_type_materializer(
    Selector(
        {
            'csv': Permissive(
                {
                    'path': Field(
                        String,
                        is_required=True,
                        description="the path in any Hadoop supported file system.",
                    ),
                    'mode': Field(
                        WriteModeOptions,
                        is_required=False,
                        description="specifies the behavior of the save operation when data already exists.",
                    ),
                    'compression': Field(
                        WriteCompressionTextOptions,
                        is_required=False,
                        description="compression codec to use when saving to file.",
                    ),
                    'sep': Field(
                        String,
                        is_required=False,
                        description="sets a single character as a separator for each field and value. If None is set, it uses the default value, ``,``.",
                    ),
                    'quote': Field(
                        String,
                        is_required=False,
                        description="""sets a single character used for escaping quoted values where the separator can be part of the value. If None is set, it uses the default value, ``"``. If an empty string is set, it uses ``u0000`` (null character).""",
                    ),
                    'escape': Field(
                        String,
                        is_required=False,
                        description="sets a single character used for escaping quotes inside an already quoted value. If None is set, it uses the default value, ``\\``.",
                    ),
                    'escapeQuotes': Field(
                        Bool,
                        is_required=False,
                        description="a flag indicating whether values containing quotes should always be enclosed in quotes. If None is set, it uses the default value ``true``, escaping all values containing a quote character.",
                    ),
                    'quoteAll': Field(
                        Bool,
                        is_required=False,
                        description="a flag indicating whether all values should always be enclosed in quotes. If None is set, it uses the default value ``false``, only escaping values containing a quote character.",
                    ),
                    'header': Field(
                        Bool,
                        is_required=False,
                        description="writes the names of columns as the first line. If None is set, it uses the default value, ``false``.",
                    ),
                    'nullValue': Field(
                        String,
                        is_required=False,
                        description="sets the string representation of a null value. If None is set, it uses the default value, empty string.",
                    ),
                    'dateFormat': Field(
                        String,
                        is_required=False,
                        description="sets the string that indicates a date format. Custom date formats follow the formats at ``java.text.SimpleDateFormat``. This applies to date type. If None is set, it uses the default value, ``yyyy-MM-dd``.",
                    ),
                    'timestampFormat': Field(
                        String,
                        is_required=False,
                        description="sets the string that indicates a timestamp format. Custom date formats follow the formats at ``java.text.SimpleDateFormat``. This applies to timestamp type. If None is set, it uses the default value, ``yyyy-MM-dd'T'HH:mm:ss.SSSXXX``.",
                    ),
                    'ignoreLeadingWhiteSpace': Field(
                        Bool,
                        is_required=False,
                        description="a flag indicating whether or not leading whitespaces from values being written should be skipped. If None is set, it uses the default value, ``true``.",
                    ),
                    'ignoreTrailingWhiteSpace': Field(
                        Bool,
                        is_required=False,
                        description="a flag indicating whether or not trailing whitespaces from values being written should be skipped. If None is set, it uses the default value, ``true``.",
                    ),
                    'charToEscapeQuoteEscaping': Field(
                        String,
                        is_required=False,
                        description="sets a single character used for escaping the escape for the quote character. If None is set, the default value is escape character when escape and quote characters are different, ``\0`` otherwise..",
                    ),
                    'encoding': Field(
                        String,
                        is_required=False,
                        description="sets the encoding (charset) of saved csv files. If None is set, the default UTF-8 charset will be used.",
                    ),
                    'emptyValue': Field(
                        String,
                        is_required=False,
                        description="sets the string representation of an empty value. If None is set, it uses the default value, ``"
                        "``.",
                    ),
                }
            ),
            'parquet': Permissive(
                {
                    'path': Field(
                        String,
                        is_required=True,
                        description="the path in any Hadoop supported file system.",
                    ),
                    'mode': Field(
                        WriteModeOptions,
                        is_required=False,
                        description="specifies the behavior of the save operation when data already exists.",
                    ),
                    'partitionBy': Field(
                        String, is_required=False, description="names of partitioning columns."
                    ),
                    'compression': Field(
                        WriteCompressionParquetOptions,
                        is_required=False,
                        description="compression codec to use when saving to file. This will override ``spark.sql.parquet.compression.codec``. If None is set, it uses the value specified in ``spark.sql.parquet.compression.codec``.",
                    ),
                }
            ),
            'json': Permissive(
                {
                    'path': Field(
                        String,
                        is_required=True,
                        description="the path in any Hadoop supported file system.",
                    ),
                    'mode': Field(
                        WriteModeOptions,
                        is_required=False,
                        description="specifies the behavior of the save operation when data already exists.",
                    ),
                    'compression': Field(
                        WriteCompressionTextOptions,
                        is_required=False,
                        description="compression codec to use when saving to file.",
                    ),
                    'dateFormat': Field(
                        String,
                        is_required=False,
                        description="sets the string that indicates a date format. Custom date formats follow the formats at ``java.text.SimpleDateFormat``. This applies to date type. If None is set, it uses the default value, ``yyyy-MM-dd``.",
                    ),
                    'timestampFormat': Field(
                        String,
                        is_required=False,
                        description="sets the string that indicates a timestamp format. Custom date formats follow the formats at ``java.text.SimpleDateFormat``. This applies to timestamp type. If None is set, it uses the default value, ``yyyy-MM-dd'T'HH:mm:ss.SSSXXX``.",
                    ),
                    'encoding': Field(
                        String,
                        is_required=False,
                        description="sets the encoding (charset) of saved csv files. If None is set, the default UTF-8 charset will be used.",
                    ),
                    'lineSep': Field(
                        String,
                        is_required=False,
                        description="defines the line separator that should be used for writing. If None is set, it uses the default value, ``\\n``.",
                    ),
                }
            ),
            'jdbc': Permissive(
                {
                    'url': Field(
                        String,
                        is_required=True,
                        description="a JDBC URL of the form ``jdbc:subprotocol:subname``.",
                    ),
                    'table': Field(
                        String,
                        is_required=True,
                        description="Name of the table in the external database.",
                    ),
                    'mode': Field(
                        WriteModeOptions,
                        is_required=False,
                        description="specifies the behavior of the save operation when data already exists.",
                    ),
                    'properties': Field(
                        Permissive(),
                        is_required=False,
                        description="""a dictionary of JDBC database connection arguments. Normally at least properties "user" and "password" with their corresponding values. For example { 'user' : 'SYSTEM', 'password' : 'mypassword' }.""",
                    ),
                }
            ),
            'orc': Permissive(
                {
                    'path': Field(
                        String,
                        is_required=True,
                        description="the path in any Hadoop supported file system.",
                    ),
                    'mode': Field(
                        WriteModeOptions,
                        is_required=False,
                        description="specifies the behavior of the save operation when data already exists.",
                    ),
                    'partitionBy': Field(
                        String, is_required=False, description="names of partitioning columns."
                    ),
                    'compression': Field(
                        WriteCompressionOrcOptions,
                        is_required=False,
                        description="compression codec to use when saving to file. This will override ``orc.compress`` and ``spark.sql.orc.compression.codec``. If None is set, it uses the value specified in ``spark.sql.orc.compression.codec``.",
                    ),
                }
            ),
            'saveAsTable': Permissive(
                {
                    'name': Field(String, is_required=True, description="the table name."),
                    'format': Field(
                        String, is_required=False, description="the format used to save."
                    ),
                    'mode': Field(
                        WriteModeOptions,
                        is_required=False,
                        description="specifies the behavior of the save operation when data already exists.",
                    ),
                    'partitionBy': Field(
                        String, is_required=False, description="names of partitioning columns."
                    ),
                    'options': Field(
                        Permissive(), is_required=False, description="all other string options."
                    ),
                }
            ),
            'text': Permissive(
                {
                    'path': Field(
                        String,
                        is_required=True,
                        description="he path in any Hadoop supported file system.",
                    ),
                    'compression': Field(
                        WriteCompressionTextOptions,
                        is_required=False,
                        description="compression codec to use when saving to file. This will override ``orc.compress`` and ``spark.sql.orc.compression.codec``. If None is set, it uses the value specified in ``spark.sql.orc.compression.codec``.",
                    ),
                    'lineSep': Field(
                        String,
                        is_required=False,
                        description="defines the line separator that should be used for writing. If None is set, it uses the default value, ``\\n``.",
                    ),
                }
            ),
        }
    )
)
def spark_df_materializer(_context, config, spark_df):
    file_type, file_options = list(config.items())[0]

    if file_type == 'csv':
        spark_df.write.csv(**file_options)
        return AssetMaterialization.file(file_options['path'])
    elif file_type == 'parquet':
        spark_df.write.parquet(**file_options)
        return AssetMaterialization.file(file_options['path'])
    elif file_type == 'json':
        spark_df.write.json(**file_options)
        return AssetMaterialization.file(file_options['path'])
    elif file_type == 'jdbc':
        spark_df.write.jdbc(**file_options)
        return AssetMaterialization.file(file_options['url'])
    elif file_type == 'orc':
        spark_df.write.orc(**file_options)
        return AssetMaterialization.file(file_options['path'])
    elif file_type == 'saveAsTable':
        spark_df.write.saveAsTable(**file_options)
        return AssetMaterialization.file(file_options['name'])
    elif file_type == 'text':
        spark_df.write.text(**file_options)
        return AssetMaterialization.file(file_options['path'])
    else:
        check.failed('Unsupported file type: {}'.format(file_type))


class SparkDataFrameS3StoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, system_storage_def):
        try:
            from dagster_aws.s3 import s3_system_storage, s3_intermediate_storage

            return (
                system_storage_def is s3_system_storage
                or system_storage_def is s3_intermediate_storage
            )
        except ImportError:
            return False

    @classmethod
    def set_intermediate_object(
        cls, intermediate_storage, context, _dagster_type, step_output_handle, value
    ):
        paths = ['intermediates', step_output_handle.step_key, step_output_handle.output_name]
        target_path = intermediate_storage.object_store.key_for_paths(paths)
        value.write.parquet(
            intermediate_storage.uri_for_paths(paths, protocol=cls.protocol(context))
        )
        return target_path

    @classmethod
    def get_intermediate_object(
        cls, intermediate_storage, context, _dagster_type, step_output_handle
    ):
        paths = ['intermediates', step_output_handle.step_key, step_output_handle.output_name]
        return context.resources.pyspark.spark_session.read.parquet(
            intermediate_storage.uri_for_paths(paths, protocol=cls.protocol(context))
        )

    @classmethod
    def required_resource_keys(cls):
        return frozenset({'pyspark'})

    @staticmethod
    def protocol(context):
        # pylint: disable=protected-access
        hadoopConf = context.resources.pyspark.spark_session.sparkContext._jsc.hadoopConfiguration()
        # If we're on EMR, s3 is preferred:
        # https://docs.aws.amazon.com/emr/latest/ManagementGuide/emr-plan-file-systems.html
        # Otherwise, s3a is preferred
        if hadoopConf.get('fs.s3.impl') == 'com.amazon.ws.emr.hadoop.fs.EmrFileSystem':
            return 's3://'
        else:
            return 's3a://'


class SparkDataFrameFilesystemStoragePlugin(TypeStoragePlugin):  # pylint: disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, system_storage_def):
        return (
            system_storage_def is fs_system_storage or system_storage_def is fs_intermediate_storage
        )

    @classmethod
    def set_intermediate_object(
        cls, intermediate_storage, _context, _dagster_type, step_output_handle, value
    ):
        paths = ['intermediates', step_output_handle.step_key, step_output_handle.output_name]
        target_path = os.path.join(intermediate_storage.root, *paths)
        value.write.parquet(intermediate_storage.uri_for_paths(paths))
        return target_path

    @classmethod
    def get_intermediate_object(
        cls, intermediate_storage, context, _dagster_type, step_output_handle
    ):
        paths = ['intermediates', step_output_handle.step_key, step_output_handle.output_name]
        return context.resources.pyspark.spark_session.read.parquet(
            os.path.join(intermediate_storage.root, *paths)
        )

    @classmethod
    def required_resource_keys(cls):
        return frozenset({'pyspark'})


DataFrame = PythonObjectDagsterType(
    python_type=NativeSparkDataFrame,
    name='PySparkDataFrame',
    description='A PySpark data frame.',
    auto_plugins=[SparkDataFrameS3StoragePlugin, SparkDataFrameFilesystemStoragePlugin],
    materializer=spark_df_materializer,
)
