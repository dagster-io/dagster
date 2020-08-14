from abc import ABCMeta

import six

from dagster import DagsterType, check

from .computation import Computation


class Asset(six.with_metaclass(ABCMeta)):
    def __init__(self, storage_key, path, computation):
        self._storage_key = check.str_param(storage_key, 'storage_key')
        self._path = check.tuple_param(path, 'path', of_type=str)
        self._computation = check.opt_inst_param(computation, 'computation', Computation)
        self._dagster_type = DagsterType(type_check_fn=lambda a, b: True, name='.'.join(self.path))

    @property
    def storage_key(self):
        return self._storage_key

    @property
    def path(self):
        return self._path

    @property
    def computation(self):
        return self._computation

    @property
    def dagster_type(self):
        return self._dagster_type


def source_asset(path, storage_key='default_storage'):
    '''A source asset is an asset that's not derived inside the lakehouse.  Other assets
    may depend on it, but it has no dependencies that the lakehouse is aware of.
    '''
    return Asset(storage_key=storage_key, path=path, computation=None)
