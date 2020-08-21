from collections import namedtuple

from dagster import check

from .asset import Asset


class Table(Asset):
    """A table is an asset that's a dataset in a relational store.

    It knows the set of columns that its materializations are expected to contain.
    """

    def __init__(self, storage_key, path, computation, columns):
        super(Table, self).__init__(storage_key=storage_key, path=path, computation=computation)
        self._columns = check.opt_list_param(columns, "columns", Column)

    @property
    def columns(self):
        return self._columns


def source_table(path, columns, storage_key="default_storage"):
    return Table(storage_key=storage_key, path=path, columns=columns, computation=None)


class Column(namedtuple("_Column", "name data_type")):
    pass
