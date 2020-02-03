import os
import sys
from datetime import datetime

from dagster_pyspark import pyspark_resource
from lakehouse import (
    InMemTableHandle,
    Lakehouse,
    construct_lakehouse_pipeline,
    input_table,
    pyspark_table,
)
from pyspark.sql import DataFrame as SparkDF
from pyspark.sql import Row
from pyspark.sql import types as spark_types

from dagster import file_relative_path, resource

# This is needed to common when loading from dagit
sys.path.insert(0, os.path.abspath(file_relative_path(__file__, '.')))


## Library-ish stuff


def field_to_spark_field(name, python_type) -> spark_types.StructField:
    spark_type = {
        int: spark_types.IntegerType(),
        float: spark_types.DoubleType(),
        str: spark_types.StringType(),
        datetime: spark_types.TimestampType(),
        bool: spark_types.BooleanType(),
    }[python_type]
    return spark_types.StructField(name, spark_type)


# TODO consider adding field-level descriptions
def spark_type_from_kwargs(**kwargs):
    return spark_types.StructType(
        [field_to_spark_field(name, python_type) for name, python_type in kwargs.items()]
    )


def create_column_descriptions(spark_type):
    buildme = '**Columns:**\n\n    '
    parts = []
    for spark_field in spark_type.fields:
        parts.append(
            '{name}: {type_name}'.format(
                name=spark_field.name, type_name=spark_field.dataType.typeName()
            )
        )
    return buildme + '\n    '.join(parts)


class TypedPySparkMemLakehouse(Lakehouse):
    def __init__(self):
        self.collected_tables = {}

    def hydrate(self, _context, _table_type, _table_metadata, table_handle, _dest_metadata):
        return table_handle.value

    def materialize(self, _context, table_type, _table_metadata, value):
        self.collected_tables[table_type.name] = value.collect()
        return None, InMemTableHandle(value=value)


@resource
def typed_pyspark_mem_lakehouse(_):
    return TypedPySparkMemLakehouse()


def typed_pyspark_table(spark_type, name=None, input_tables=None, description=None):
    def _wrap(fn):
        return pyspark_table(
            name=name,
            input_tables=input_tables,
            description=description + '\n\n' + create_column_descriptions(spark_type)
            if description
            else create_column_descriptions(spark_type),
        )(fn)

    return _wrap


# Library tests


def test_spark_type_from_kwargs():
    assert spark_type_from_kwargs(id=int) == spark_types.StructType(
        [spark_types.StructField('id', spark_types.IntegerType())]
    )

    assert spark_type_from_kwargs(number=int) == spark_types.StructType(
        [spark_types.StructField('number', spark_types.IntegerType())]
    )

    assert spark_type_from_kwargs(name=str) == spark_types.StructType(
        [spark_types.StructField('name', spark_types.StringType())]
    )


# Start example typed warehouse


NUMBER_TABLE_STRUCT_TYPE = spark_type_from_kwargs(id=int, number=int)


@typed_pyspark_table(spark_type=NUMBER_TABLE_STRUCT_TYPE)
def NumberTable(context) -> SparkDF:
    return context.resources.spark.spark_session.createDataFrame(
        [Row(id=1, number=2)], NUMBER_TABLE_STRUCT_TYPE
    )


STRING_TABLE_STRUCT_TYPE = spark_type_from_kwargs(id=int, string=str)


@typed_pyspark_table(spark_type=STRING_TABLE_STRUCT_TYPE)
def StringTable(context) -> SparkDF:
    return context.resources.spark.spark_session.createDataFrame(
        [Row(id=1, string='23')], STRING_TABLE_STRUCT_TYPE
    )


JOIN_TABLE_STRUCT_TYPE = spark_type_from_kwargs(id=int, number=int, string=str)


@typed_pyspark_table(
    input_tables=[input_table('number_df', NumberTable), input_table('string_df', StringTable)],
    spark_type=JOIN_TABLE_STRUCT_TYPE,
    description='Joining together of the number and the string.',
)
def JoinTable(_context, number_df: NumberTable, string_df: StringTable) -> SparkDF:
    return number_df.join(string_df, number_df.id == string_df.id, 'inner').drop(string_df.id)


def test_execute_typed_in_mem_lakehouse(execute_spark_lakehouse_build):
    lakehouse = TypedPySparkMemLakehouse()
    pipeline_result = execute_spark_lakehouse_build(
        tables=[NumberTable, StringTable, JoinTable], lakehouse=lakehouse
    )

    assert pipeline_result.success
    # Row ordering varies on 3.5 - compare as dicts
    assert (
        lakehouse.collected_tables['JoinTable'][0].asDict()
        == Row(id=1, number=2, string='23').asDict()
    )


# for dagit
typed_lakehouse_pipeline = construct_lakehouse_pipeline(
    name='typed_lakehouse_pipeline',
    lakehouse_tables=[NumberTable, StringTable, JoinTable],
    resources={'lakehouse': typed_pyspark_mem_lakehouse, 'spark': pyspark_resource},
)
