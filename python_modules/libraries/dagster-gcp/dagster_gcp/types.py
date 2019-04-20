import re
import six

from google.cloud.bigquery.job import (
    CreateDisposition,
    SchemaUpdateOption,
    QueryPriority,
    WriteDisposition,
)

from dagster import DagsterUserError, Enum, EnumValue, ConfigScalar


# Project names are permitted to have alphanumeric, dashes and underscores, up to 1024 characters.
RE_PROJECT = r'[\w\d\-\_]{1,1024}'

# Datasets and tables are permitted to have alphanumeric or underscores, no dashes allowed, up to
# 1024 characters
RE_DS_TABLE = r'[\w\d\_]{1,1024}'


BQCreateDispositionCreateIfNeeded = EnumValue(CreateDisposition.CREATE_IF_NEEDED)
BQCreateDispositionCreateNever = EnumValue(CreateDisposition.CREATE_NEVER)
BQCreateDisposition = Enum(
    name='BQCreateDisposition',
    enum_values=[BQCreateDispositionCreateIfNeeded, BQCreateDispositionCreateNever],
)

BQPriorityBatch = EnumValue(QueryPriority.BATCH)
BQPriorityInteractive = EnumValue(QueryPriority.INTERACTIVE)
BQPriority = Enum(name='BQPriority', enum_values=[BQPriorityBatch, BQPriorityInteractive])

BQSchemaUpdateOptionAllowFieldAddition = EnumValue(
    SchemaUpdateOption.ALLOW_FIELD_ADDITION,
    description='Allow adding a nullable field to the schema.',
)
BQSchemaUpdateOptionAllowFieldRelaxation = EnumValue(
    SchemaUpdateOption.ALLOW_FIELD_RELAXATION,
    description='Allow relaxing a required field in the original schema to nullable.',
)
BQSchemaUpdateOption = Enum(
    name='BQSchemaUpdateOption',
    enum_values=[BQSchemaUpdateOptionAllowFieldAddition, BQSchemaUpdateOptionAllowFieldRelaxation],
)

BQWriteDispositionWriteAppend = EnumValue(WriteDisposition.WRITE_APPEND)
BQWriteDispositionWriteEmpty = EnumValue(WriteDisposition.WRITE_EMPTY)
BQWriteDispositionWriteTruncate = EnumValue(WriteDisposition.WRITE_TRUNCATE)
BQWriteDisposition = Enum(
    name='BQWriteDisposition',
    enum_values=[
        BQWriteDispositionWriteAppend,
        BQWriteDispositionWriteEmpty,
        BQWriteDispositionWriteTruncate,
    ],
)


class Dataset(ConfigScalar):
    def __init__(self):
        super(Dataset, self).__init__(key=type(self).__name__, name=type(self).__name__)

    def is_config_scalar_valid(self, config_value):
        if not isinstance(config_value, six.string_types):
            return False

        # Must be of form "project.dataset" or "dataset"
        return re.match(
            r'^' + RE_PROJECT + r'\.' + RE_DS_TABLE + r'$|^' + RE_DS_TABLE + r'$', config_value
        )


class Table(ConfigScalar):
    def __init__(self):
        super(Table, self).__init__(key=type(self).__name__, name=type(self).__name__)

    def is_config_scalar_valid(self, config_value):
        if not isinstance(config_value, six.string_types):
            return False

        # Must be of form "project.dataset.table" or "dataset.table"
        return re.match(
            r'^'
            + RE_PROJECT
            + r'\.'
            + RE_DS_TABLE
            + r'\.'
            + RE_DS_TABLE
            + r'$|^'
            + RE_DS_TABLE
            + r'\.'
            + RE_DS_TABLE
            + r'$',
            config_value,
        )


class BigQueryError(DagsterUserError):
    pass
