"""
A lakehouse models the relationships between a set of data assets,
storages, and environments.

A lakehouse can generate Dagster pipelines that update the contents of
its assets.
"""

from .asset import Asset, source_asset
from .computation import Computation
from .decorators import computed_asset, computed_table
from .house import Lakehouse
from .multi_type_storage import multi_type_asset_storage
from .storage import AssetStorage
from .table import Column, Table, source_table
