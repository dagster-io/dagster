from .house import Lakehouse
from .table import create_lakehouse_table_def


# So in this case because data processing is totally within the data warehouse
# These are complete and total no-ops
class SqlLiteLakehouse(Lakehouse):
    def __init__(self):
        pass

    def hydrate(self, _context, _table_type, _table_metadata, table_handle, _dest_metadata):
        return None

    def materialize(self, context, table_type, table_metadata, value):
        return None, None


def sqlite_table(name=None, input_tables=None, other_input_defs=None, tags=None, description=None):
    if callable(name):
        fn = name
        return create_lakehouse_table_def(
            name=fn.__name__, lakehouse_fn=fn, input_tables=[], required_resource_keys={'conn'}
        )

    def _wrap(fn):
        return create_lakehouse_table_def(
            name=name if name is not None else fn.__name__,
            lakehouse_fn=fn,
            input_tables=input_tables,
            other_input_defs=other_input_defs,
            tags=tags,
            description=description,
            required_resource_keys={'conn'},
        )

    return _wrap
