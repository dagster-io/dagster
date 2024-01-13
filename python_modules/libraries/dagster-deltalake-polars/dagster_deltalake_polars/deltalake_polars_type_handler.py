from typing import Any, Dict, Optional, Sequence, Tuple, Type

import polars as pl
import pyarrow as pa
from dagster._annotations import experimental
from dagster._core.storage.db_io_manager import (
    DbTypeHandler,
)
from dagster_deltalake.handler import (
    DeltalakeBaseArrowTypeHandler,
    DeltaLakePyArrowTypeHandler,
)
from dagster_deltalake.io_manager import DeltaLakeIOManager


@experimental
class DeltaLakePolarsTypeHandler(DeltalakeBaseArrowTypeHandler[pl.DataFrame]):
    def from_arrow(
        self, obj: pa.RecordBatchReader, target_type: Type[pl.DataFrame]
    ) -> pl.DataFrame:
        return pl.from_arrow(obj)  # type: ignore

    def to_arrow(self, obj: pl.DataFrame) -> Tuple[pa.RecordBatchReader, Dict[str, Any]]:
        return obj.to_arrow().to_reader(), {"large_dtypes": True}

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [pl.DataFrame]


@experimental
class DeltaLakePolarsIOManager(DeltaLakeIOManager):
    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DeltaLakePolarsTypeHandler(), DeltaLakePyArrowTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[Type]:
        return pl.DataFrame
