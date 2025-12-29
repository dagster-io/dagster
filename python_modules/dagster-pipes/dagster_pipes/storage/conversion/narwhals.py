from typing import Any

import narwhals as nw
from narwhals.dataframe import BaseFrame
from narwhals.typing import IntoFrame
from typing_extensions import TypeVar

from dagster_pipes.storage.conversion.type_utils import (
    get_all_dataframe_types,
    get_dataframe_target_types,
    get_pandas_dataframe_type,
    get_polars_dataframe_type,
    get_pyarrow_table_type,
)

TTarget = TypeVar("TTarget")


class NarwhalsDataFrameConverter:
    """Converter used for StorageAdapters that use Narwhals DataFrames/LazyFrames as their native type."""

    def can_convert_for_load(self, raw_type: type[IntoFrame], target_type: type) -> bool:
        if raw_type == target_type:
            return True

        return raw_type in get_all_dataframe_types() and target_type in get_dataframe_target_types()

    def convert_for_load(self, obj: IntoFrame, target_type: type[TTarget]) -> TTarget:
        if isinstance(obj, target_type):
            return obj

        nw_obj = nw.from_native(obj)
        if isinstance(nw_obj, nw.LazyFrame):
            nw_obj = nw_obj.collect()

        if target_type is get_pyarrow_table_type():
            return nw_obj.to_arrow()  # type: ignore[no-any-return]
        elif target_type is get_pandas_dataframe_type():
            return nw_obj.to_pandas()  # type: ignore[no-any-return]
        elif target_type is get_polars_dataframe_type():
            return nw_obj.to_polars()  # type: ignore[no-any-return]
        else:
            raise ValueError(f"Cannot convert {type(obj).__name__} to {target_type.__name__}")

    def can_convert_for_store(self, obj: Any, raw_type: type[IntoFrame]) -> bool:
        if isinstance(obj, raw_type):
            return True
        elif not issubclass(raw_type, BaseFrame):
            return False

        try:
            nw_obj = nw.from_native(obj)
            return isinstance(nw_obj, raw_type)
        except TypeError:
            return False

    def convert_for_store(self, obj: Any, to_type: type[BaseFrame]) -> Any:
        if isinstance(obj, to_type):
            return obj
        return nw.from_native(obj)
