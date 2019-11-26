import os

import pytest
from dagster_pyspark import pyspark_resource
from lakehouse import Lakehouse, construct_lakehouse_pipeline

from dagster import Materialization, check, execute_pipeline


class LocalOnDiskSparkCsvLakehouse(Lakehouse):
    def __init__(self, root_dir):
        self.lakehouse_path = check.str_param(root_dir, 'root_dir')

    def _path_for_table(self, table_type):
        return os.path.join(self.lakehouse_path, table_type.name)

    def hydrate(self, context, table_type, _table_metadata, _table_handle, _dest_metadata):
        path = self._path_for_table(table_type)
        return context.resources.spark.spark_session.read.csv(path, header=True, inferSchema=True)

    def materialize(self, _context, table_type, _table_metadata, value):
        path = self._path_for_table(table_type)
        value.write.csv(path=path, header=True, mode='overwrite')
        return Materialization.file(path), None


@pytest.fixture(scope='session')
def local_on_disk_spark_lakehouse():
    return LocalOnDiskSparkCsvLakehouse


@pytest.fixture(scope='session')
def execute_spark_lakehouse_build():
    def _execute_spark_lakehouse_build(tables, lakehouse, environment_dict=None):
        return execute_pipeline(
            construct_lakehouse_pipeline(
                name='spark_lakehouse_pipeline',
                lakehouse_tables=tables,
                resources={'lakehouse': lakehouse, 'spark': pyspark_resource},
            ),
            environment_dict=environment_dict,
        )

    return _execute_spark_lakehouse_build
