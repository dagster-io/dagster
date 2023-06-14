from typing import Optional, Sequence, Type

import polars as pl
import pyarrow as pa
from dagster._core.storage.db_io_manager import (
    DbTypeHandler,
)
from dagster_deltalake.handler import DeltalakeBaseArrowTypeHandler
from dagster_deltalake.io_manager import DeltaLakeIOManager


class DeltaLakePolarsTypeHandler(DeltalakeBaseArrowTypeHandler[pl.DataFrame]):
    def from_arrow(self, obj: pa.RecordBatchReader, target_type: Type[pl.DataFrame]) -> pl.DataFrame:
        table = pl.from_arrow(obj.read_all())
        assert isinstance(table, pl.DataFrame) # making sure for pyright's sake
        return table

    def to_arrow(self, obj: pl.DataFrame) -> pa.RecordBatchReader:
        return obj.to_arrow().to_reader()

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [pl.DataFrame]


class DeltaLakePolarsIOManager(DeltaLakeIOManager):
    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DeltaLakePolarsTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[Type]:
        return pl.DataFrame
