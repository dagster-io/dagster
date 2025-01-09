from collections.abc import Sequence
from typing import Any, Optional, Union

import polars as pl
import pyarrow as pa
import pyarrow.dataset as ds
from dagster import InputContext
from dagster._core.storage.db_io_manager import DbTypeHandler, TableSlice
from dagster_deltalake.handler import (
    DeltalakeBaseArrowTypeHandler,
    DeltaLakePyArrowTypeHandler,
    _table_reader,
)
from dagster_deltalake.io_manager import DeltaLakeIOManager, TableConnection

PolarsTypes = Union[pl.DataFrame, pl.LazyFrame]


class DeltaLakePolarsTypeHandler(DeltalakeBaseArrowTypeHandler[PolarsTypes]):
    def from_arrow(
        self,
        obj: Union[ds.Dataset, pa.RecordBatchReader],
        target_type: type[PolarsTypes],
    ) -> PolarsTypes:
        if isinstance(obj, pa.RecordBatchReader):
            return pl.DataFrame(obj.read_all())
        elif isinstance(obj, ds.Dataset):
            df = pl.scan_pyarrow_dataset(obj)
            if target_type == pl.DataFrame:
                return df.collect()
            else:
                return df
        else:
            raise NotImplementedError("Unsupported objected passed of type:  %s", type(obj))

    def to_arrow(self, obj: PolarsTypes) -> tuple[pa.RecordBatchReader, dict[str, Any]]:
        if isinstance(obj, pl.LazyFrame):
            obj = obj.collect()
        return obj.to_arrow().to_reader(), {"large_dtypes": True}

    def load_input(
        self,
        context: InputContext,
        table_slice: TableSlice,
        connection: TableConnection,
    ) -> PolarsTypes:
        """Loads the input as a Polars DataFrame or LazyFrame."""
        dataset = _table_reader(table_slice, connection)

        if table_slice.columns is not None:
            if context.dagster_type.typing_type == pl.LazyFrame:
                return self.from_arrow(dataset, context.dagster_type.typing_type).select(
                    table_slice.columns
                )
            else:
                scanner = dataset.scanner(columns=table_slice.columns)
                return self.from_arrow(scanner.to_reader(), context.dagster_type.typing_type)
        else:
            return self.from_arrow(dataset, context.dagster_type.typing_type)

    @property
    def supported_types(self) -> Sequence[type[object]]:
        return [pl.DataFrame, pl.LazyFrame]


class DeltaLakePolarsIOManager(DeltaLakeIOManager):
    @staticmethod
    def type_handlers() -> Sequence[DbTypeHandler]:
        return [DeltaLakePolarsTypeHandler(), DeltaLakePyArrowTypeHandler()]

    @staticmethod
    def default_load_type() -> Optional[type]:
        return pl.DataFrame
