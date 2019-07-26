from dagster import resource, check
from pyspark.sql import DataFrame

from .house import Lakehouse
from .table import InMemTableHandle, create_lakehouse_table_def


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


def pyspark_table(
    name=None, input_tables=None, other_input_defs=None, metadata=None, description=None
):
    if callable(name):
        fn = name
        return create_lakehouse_table_def(
            name=fn.__name__, lakehouse_fn=fn, input_tables=[], required_resource_keys={'spark'}
        )

    def _wrap(fn):
        return create_lakehouse_table_def(
            name=name if name is not None else fn.__name__,
            lakehouse_fn=fn,
            input_tables=input_tables,
            other_input_defs=other_input_defs,
            metadata=metadata,
            description=description,
            required_resource_keys={'spark'},
        )

    return _wrap
