from dagster import resource, check
from pyspark.sql import DataFrame

from .house import Lakehouse
from .table import InMemTableHandle


class PySparkMemLakehouse(Lakehouse):
    def __init__(self):
        self.collected_tables = {}

    def hydrate(self, _context, _table_type, _table_metadata, table_handle):
        check.inst_param(table_handle, 'table_handle', InMemTableHandle)

        return table_handle.value

    def materialize(self, context, table_type, table_metadata, value):
        check.inst_param(value, 'value', DataFrame)

        self.collected_tables[table_type.name] = value.collect()
        return None, InMemTableHandle(value=value)


@resource
def pyspark_mem_lakehouse_resource(_):
    return PySparkMemLakehouse()
