from abc import ABCMeta
from collections import namedtuple

import six

from dagster import DagsterType, check


class Asset(six.with_metaclass(ABCMeta)):
    def __init__(self, storage_key, path):
        self._storage_key = check.str_param(storage_key, 'storage_key')
        self._path = check.tuple_param(path, 'path', of_type=str)
        self._dagster_type = DagsterType(type_check_fn=lambda a, b: True, name='.'.join(self.path))

    @property
    def storage_key(self):
        return self._storage_key

    @property
    def path(self):
        return self._path

    @property
    def dagster_type(self):
        return self._dagster_type


class AssetDependency(namedtuple('_AssetDependency', 'asset in_memory_type')):
    '''An asset dependency describes how the contents of another asset are provided to a
    ComputedAsset's compute_fn.

    Attributes:
        asset (Asset): The asset that we depend on.
        in_memory_type (Type): The type, e.g. pandas.DataFrame, that the asset's contents should be
            hydrated into to be passed as the compute_fn.
    '''


class SourceAsset(Asset):
    '''A source asset is an asset that's not derived inside the lakehouse.  Other assets
    may depend on it, but it has no dependencies that the lakehouse is aware of.
    '''


class ComputedAsset(Asset):
    '''A derived asset combines an address in persistent storage with the computation
    responsible for producing the object stored at that address: e.g. the name of a database table
    and a SQL query that produces its contents, or the name of an ML model and the python code
    that trains it.

    An asset is agnostic to the physical details of where it's stored and how it's saved to
    and loaded from that storage. The Lakehouse that the asset resides in is responsible for
    those.

    Attributes:
        storage_key (str): The name of the storage that the asset resides in.
        path (Tuple[str, ...]): The address of the object within the given storage.
        compute_fn (Callable): A python function with no side effects that produces an in-memory
            representation of the asset's contents from in-memory representation of the
            asset' inputs.
        deps (Dict[str, AssetDependency]): The assets that the compute_fn depends on
            to produce the asset's contents, keyed by their arg names in the compute_fn
            definition.
        output_in_memory_type (Type): The python type that the compute_fn will return.
    '''

    def __init__(self, storage_key, path, compute_fn, deps, output_in_memory_type):
        self._compute_fn = check.callable_param(compute_fn, 'compute_fn')
        self._deps = check.dict_param(deps, 'deps', key_type=str, value_type=AssetDependency)
        self._output_in_memory_type = check.inst_param(
            output_in_memory_type, 'output_in_memory_type', type
        )

        super(ComputedAsset, self).__init__(
            storage_key=check.str_param(storage_key, 'storage_key'),
            path=check.tuple_param(path, 'path', of_type=str),
        )

    @property
    def compute_fn(self):
        return self._compute_fn

    @property
    def deps(self):
        return self._deps

    @property
    def output_in_memory_type(self):
        return self._output_in_memory_type
