from collections.abc import Sequence
from typing import Any, Optional

import pandas as pd
import pyarrow as pa
from dagster._core.storage.db_io_manager import DbTypeHandler
from dagster_deltalake.handler import DeltalakeBaseArrowTypeHandler, DeltaLakePyArrowTypeHandler
from dagster_deltalake.io_manager import DeltaLakeIOManager


class DeltaLakePandasTypeHandler(DeltalakeBaseArrowTypeHandler[pd.DataFrame]):
    def from_arrow(
        self, obj: pa.RecordBatchReader, target_type: type[pd.DataFrame]
    ) -> pd.DataFrame:
        return obj.read_pandas()

    def to_arrow(self, obj: pd.DataFrame) -> tuple[pa.RecordBatchReader, dict[str, Any]]:
        return pa.Table.from_pandas(obj).to_reader(), {}

    @property
    def supported_types(self) -> Sequence[type[object]]:
        return [pd.DataFrame]


class DeltaLakePandasIOManager(DeltaLakeIOManager):
    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DeltaLakePandasTypeHandler(), DeltaLakePyArrowTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pd.DataFrame
