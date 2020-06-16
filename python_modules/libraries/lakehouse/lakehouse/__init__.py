'''
A lakehouse models the relationships between a set of data assets,
storages, and environments.

A lakehouse can generate Dagster pipelines that update the contents of
its assets.
'''

from .asset import ComputedAsset, SourceAsset
from .decorators import computed_asset
from .house import Lakehouse, TypeStoragePolicy
