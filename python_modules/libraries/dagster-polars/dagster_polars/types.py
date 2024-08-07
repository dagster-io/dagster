import sys
from typing import Dict

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias

import polars as pl

DataFramePartitions: TypeAlias = Dict[str, pl.DataFrame]
LazyFramePartitions: TypeAlias = Dict[str, pl.LazyFrame]

__all__ = [
    "DataFramePartitions",
    "LazyFramePartitions",
]
