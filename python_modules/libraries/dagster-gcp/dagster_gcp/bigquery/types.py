import re
from enum import Enum as PyEnum

from google.cloud.bigquery.job import (
    CreateDisposition,
    Encoding,
    QueryPriority,
    SchemaUpdateOption,
    SourceFormat,
    WriteDisposition,
)

from dagster import Enum, EnumValue
from dagster._config import ConfigScalar, ConfigScalarKind, PostProcessingError


class BigQueryLoadSource(PyEnum):
    DataFrame = "DATA_FRAME"
    GCS = "GCS"
    File = "FILE"


BQCreateDisposition = Enum(
    name="BQCreateDisposition",
    enum_values=[
        EnumValue(CreateDisposition.CREATE_IF_NEEDED),
        EnumValue(CreateDisposition.CREATE_NEVER),
    ],
)

BQPriority = Enum(
    name="BQPriority",
    enum_values=[EnumValue(QueryPriority.BATCH), EnumValue(QueryPriority.INTERACTIVE)],
)

BQSchemaUpdateOption = Enum(
    name="BQSchemaUpdateOption",
    enum_values=[
        EnumValue(
            SchemaUpdateOption.ALLOW_FIELD_ADDITION,
            description="Allow adding a nullable field to the schema.",
        ),
        EnumValue(
            SchemaUpdateOption.ALLOW_FIELD_RELAXATION,
            description="Allow relaxing a required field in the original schema to nullable.",
        ),
    ],
)

BQWriteDisposition = Enum(
    name="BQWriteDisposition",
    enum_values=[
        EnumValue(WriteDisposition.WRITE_APPEND),
        EnumValue(WriteDisposition.WRITE_EMPTY),
        EnumValue(WriteDisposition.WRITE_TRUNCATE),
    ],
)

BQEncoding = Enum(
    name="BQEncoding", enum_values=[EnumValue(Encoding.ISO_8859_1), EnumValue(Encoding.UTF_8)]
)

BQSourceFormat = Enum(
    name="BQSourceFormat",
    enum_values=[
        EnumValue(SourceFormat.AVRO),
        EnumValue(SourceFormat.CSV),
        EnumValue(SourceFormat.DATASTORE_BACKUP),
        EnumValue(SourceFormat.NEWLINE_DELIMITED_JSON),
        EnumValue(SourceFormat.ORC),
        EnumValue(SourceFormat.PARQUET),
    ],
)


# Project names are permitted to have alphanumeric, dashes and underscores, up to 1024 characters.
RE_PROJECT = r"[\w\d\-\_]{1,1024}"

# Datasets and tables are permitted to have alphanumeric or underscores, no dashes allowed, up to
# 1024 characters
RE_DS_TABLE = r"[\w\d\_]{1,1024}"

# BigQuery supports writes directly to date partitions with the syntax foo.bar$20190101
RE_PARTITION_SUFFIX = r"(\$\d{8})?"


def _is_valid_dataset(config_value):
    """Datasets must be of form "project.dataset" or "dataset" """
    return re.match(
        # regex matches: project.dataset -- OR -- dataset
        r"^" + RE_PROJECT + r"\." + RE_DS_TABLE + r"$|^" + RE_DS_TABLE + r"$",
        config_value,
    )


def _is_valid_table(config_value):
    """Tables must be of form "project.dataset.table" or "dataset.table" with optional
    date-partition suffix
    """
    return re.match(
        r"^"
        + RE_PROJECT  #          project
        + r"\."  #               .
        + RE_DS_TABLE  #         dataset
        + r"\."  #               .
        + RE_DS_TABLE  #         table
        + RE_PARTITION_SUFFIX  # date partition suffix
        + r"$|^"  #              -- OR --
        + RE_DS_TABLE  #         dataset
        + r"\."  #               .
        + RE_DS_TABLE  #         table
        + RE_PARTITION_SUFFIX  # date partition suffix
        + r"$",
        config_value,
    )


class _Dataset(ConfigScalar):
    def __init__(self):
        super(_Dataset, self).__init__(
            key=type(self).__name__,
            given_name=type(self).__name__,
            scalar_kind=ConfigScalarKind.STRING,
        )

    def post_process(self, value):
        if not _is_valid_dataset(value):
            raise PostProcessingError('Datasets must be of the form "project.dataset" or "dataset"')
        return value


class _Table(ConfigScalar):
    def __init__(self):
        super(_Table, self).__init__(
            key=type(self).__name__,
            given_name=type(self).__name__,
            scalar_kind=ConfigScalarKind.STRING,
        )

    def post_process(self, value):
        if not _is_valid_table(value):
            raise PostProcessingError(
                (
                    'Tables must be of the form "project.dataset.table" or "dataset.table" '
                    "with optional date-partition suffix"
                )
            )

        return value


# https://github.com/dagster-io/dagster/issues/1971
Table = _Table()
Dataset = _Dataset()


class BigQueryError(Exception):
    pass
