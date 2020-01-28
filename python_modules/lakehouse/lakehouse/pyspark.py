from pyspark.sql import DataFrame

from dagster import check, resource

from .house import Lakehouse
from .table import InMemTableHandle, create_lakehouse_table_def


class PySparkMemLakehouse(Lakehouse):
    def __init__(self):
        self.collected_tables = {}

    def hydrate(self, _context, table_type, _table_metadata, table_handle, _dest_metadata):
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
    name=None,
    input_tables=None,
    other_input_defs=None,
    tags=None,
    required_resource_keys=None,
    description=None,
):
    required_resource_keys = check.opt_set_param(required_resource_keys, 'required_resource_keys')
    required_resource_keys.add('spark')
    tags = check.opt_dict_param(tags, 'tags')
    tags['lakehouse_type'] = 'pyspark_table'
    tags['kind'] = 'pyspark'

    if callable(name):
        fn = name
        return create_lakehouse_table_def(
            name=fn.__name__,
            lakehouse_fn=fn,
            input_tables=[],
            required_resource_keys=required_resource_keys,
            tags=tags,
        )

    def _wrap(fn):
        return create_lakehouse_table_def(
            name=name if name is not None else fn.__name__,
            lakehouse_fn=fn,
            input_tables=input_tables,
            other_input_defs=other_input_defs,
            tags=tags,
            description=description,
            required_resource_keys=required_resource_keys,
        )

    return _wrap
