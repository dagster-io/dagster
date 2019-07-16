from dagster import resource

from .house import Lakehouse
from .table import InMemTableHandle


class PySparkMemLakehouse(Lakehouse):
    def __init__(self):
        self.collected_tables = {}

    def hydrate(self, _context, _table_type, _table_metadata, table_handle):
        return table_handle.value

    def materialize(self, _context, table_type, _table_metadata, value):
        self.collected_tables[table_type.name] = value.collect()
        return None, InMemTableHandle(value=value)


@resource
def pyspark_mem_lakehouse_resource(_):
    return PySparkMemLakehouse()
