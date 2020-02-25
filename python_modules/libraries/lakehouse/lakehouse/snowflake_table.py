from dagster import check

from .house import Lakehouse
from .table import create_lakehouse_table_def


class SnowflakeLakehouse(Lakehouse):
    def __init__(self):
        pass

    def hydrate(self, _context, _table_type, _table_metadata, table_handle, _dest_metadata):
        return None

    def materialize(self, context, table_type, table_metadata, value):
        return None, None


def snowflake_table(
    name=None,
    input_tables=None,
    other_input_defs=None,
    tags=None,
    required_resource_keys=None,
    description=None,
):
    tags = check.opt_dict_param(tags, 'tags')
    tags['lakehouse_type'] = 'snowflake_table'
    tags['kind'] = 'snowflake'

    required_resource_keys = check.opt_set_param(required_resource_keys, 'required_resource_keys')
    required_resource_keys.add('snowflake')

    if callable(name):
        fn = name
        return create_lakehouse_table_def(
            name=fn.__name__,
            lakehouse_fn=fn,
            input_tables=[],
            required_resource_keys=required_resource_keys,
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
