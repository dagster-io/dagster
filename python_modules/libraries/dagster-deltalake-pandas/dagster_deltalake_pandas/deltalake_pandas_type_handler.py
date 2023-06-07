from typing import Optional, Sequence, Type

import pandas as pd
import pyarrow as pa
from dagster._core.storage.db_io_manager import (
    DbTypeHandler,
)
from dagster_deltalake.handler import DeltalakeBaseArrowTypeHandler
from dagster_deltalake.io_manager import DeltaLakeIOManager


class DeltaLakePandasTypeHandler(DeltalakeBaseArrowTypeHandler[pd.DataFrame]):
    def from_arrow(
        self, obj: pa.RecordBatchReader, target_type: Type[pd.DataFrame]
    ) -> pd.DataFrame:
        return obj.read_pandas()

    def to_arrow(self, obj: pd.DataFrame) -> pa.RecordBatchReader:
        return pa.Table.from_pandas(obj).to_reader()

    @property
    def supported_types(self) -> Sequence[Type[object]]:
        return [pd.DataFrame]


class DeltaLakePandasIOManager(DeltaLakeIOManager):
    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DeltaLakePandasTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[Type]:
        return pd.DataFrame
