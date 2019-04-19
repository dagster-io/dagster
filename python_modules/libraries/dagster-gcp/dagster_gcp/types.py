import six

from dagster import Enum, EnumValue, ConfigScalar

from google.cloud.bigquery.job import (
    CreateDisposition,
    SchemaUpdateOption,
    QueryPriority,
    WriteDisposition,
)


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


class BQDataset(ConfigScalar):
    def __init__(self):
        super(BQDataset, self).__init__(key=type(self).__name__, name=type(self).__name__)

    def is_config_scalar_valid(self, config_value):
        if not isinstance(config_value, six.string_types):
            return False

        # Must be of form "project.dataset"
        split = config_value.split('.')
        return len(split) == 2 and [len(x) >= 1 for x in split]
