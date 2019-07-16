import os

from dagster import Materialization, check, ResourceDefinition, ModeDefinition, execute_pipeline
from dagster_pyspark import spark_session_resource

from lakehouse import construct_lakehouse_pipeline


class LocalOnDiskSparkCsvLakehouse:
    def __init__(self, root_dir):
        self.lakehouse_path = check.str_param(root_dir, 'root_dir')

    def _path_for_table(self, table_type):
        return os.path.join(self.lakehouse_path, table_type.name)

    def hydrate(self, context, table_type, _table_metadata, _table_handle):
        path = self._path_for_table(table_type)
        return context.resources.spark.read.csv(path, header=True, inferSchema=True)

    def materialize(self, _context, table_type, _table_metadata, value):
        path = self._path_for_table(table_type)
        value.write.csv(path=path, header=True, mode='overwrite')
        return Materialization.file(path), None


def execute_spark_lakehouse_build(tables, lakehouse, environment_dict=None):
    return execute_pipeline(
        construct_lakehouse_pipeline(
            name='spark_lakehouse_pipeline',
            lakehouse_tables=tables,
            mode_defs=[
                ModeDefinition(
                    resource_defs={
                        'spark': spark_session_resource,
                        'lakehouse': ResourceDefinition.hardcoded_resource(lakehouse),
                    }
                )
            ],
        ),
        environment_dict=environment_dict,
    )
