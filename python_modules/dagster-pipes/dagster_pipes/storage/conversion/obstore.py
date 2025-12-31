"""Type converter for object store data formats."""

import io
import pickle
from typing import Any

from typing_extensions import TypeVar

from dagster_pipes.storage.conversion.narwhals import NarwhalsDataFrameConverter
from dagster_pipes.storage.conversion.type_utils import (
    get_dataframe_target_types,
    get_pandas_dataframe_type,
    get_polars_dataframe_type,
)

TTarget = TypeVar("TTarget")


# File extension to format mapping
EXTENSION_TO_FORMAT: dict[str, str] = {
    ".parquet": "parquet",
    ".pq": "parquet",
    ".pkl": "pickle",
    ".pickle": "pickle",
    ".json": "json",
    ".jsonl": "json",
    ".csv": "csv",
    ".txt": "text",
    ".text": "text",
}


def infer_format_from_path(path: str) -> str:
    """Infer format from file extension.

    Returns 'bytes' if no recognized extension is found.
    """
    path_lower = path.lower()
    for ext, fmt in EXTENSION_TO_FORMAT.items():
        if path_lower.endswith(ext):
            return fmt
    return "bytes"


class ObjectStoreConverter:
    """Converts between object store bytes and Python types.

    Supports multiple formats:
    - parquet: DataFrames (pandas, polars, pyarrow)
    - csv: DataFrames (pandas, polars, pyarrow)
    - json: dicts, lists, or DataFrames
    - pickle: any Python object
    - text: str
    - bytes: raw bytes

    For DataFrame formats (parquet, csv), composes with NarwhalsDataFrameConverter.
    Subclass to add custom format handlers.
    """

    SUPPORTED_FORMATS = {"parquet", "csv", "json", "pickle", "bytes", "text"}

    def __init__(self):
        self._narwhals = NarwhalsDataFrameConverter()

    def can_load(self, fmt: str, target_type: type) -> bool:
        """Check if we can load data in the given format as the target type."""
        if fmt == "parquet":
            return target_type in get_dataframe_target_types()
        elif fmt == "csv":
            return target_type in get_dataframe_target_types()
        elif fmt == "json":
            # JSON can be loaded as dict, list, or DataFrame
            return target_type in (dict, list, *get_dataframe_target_types())
        elif fmt == "pickle":
            # Pickle can be unpickled to any type
            return True
        elif fmt == "bytes":
            return target_type is bytes
        elif fmt == "text":
            return target_type is str
        return False

    def load(self, data: bytes, fmt: str, target_type: type[TTarget]) -> TTarget:
        """Load bytes data in the given format and convert to target type."""
        if fmt == "parquet":
            return self._load_parquet(data, target_type)
        elif fmt == "csv":
            return self._load_csv(data, target_type)
        elif fmt == "json":
            return self._load_json(data, target_type)
        elif fmt == "pickle":
            return pickle.loads(data)
        elif fmt == "bytes":
            return data  # type: ignore[return-value]
        elif fmt == "text":
            return data.decode("utf-8")  # type: ignore[return-value]
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    def can_store(self, obj: Any, fmt: str) -> bool:
        """Check if we can store the given object in the specified format."""
        if fmt == "parquet":
            return self._is_dataframe(obj)
        elif fmt == "csv":
            return self._is_dataframe(obj)
        elif fmt == "json":
            # JSON can store dicts, lists, or DataFrames
            return isinstance(obj, (dict, list)) or self._is_dataframe(obj)
        elif fmt == "pickle":
            # Pickle can store anything
            return True
        elif fmt == "bytes":
            return isinstance(obj, bytes)
        elif fmt == "text":
            return isinstance(obj, str)
        return False

    def serialize(self, obj: Any, fmt: str) -> bytes:
        """Serialize object to bytes in the given format."""
        if fmt == "parquet":
            return self._serialize_parquet(obj)
        elif fmt == "csv":
            return self._serialize_csv(obj)
        elif fmt == "json":
            return self._serialize_json(obj)
        elif fmt == "pickle":
            return pickle.dumps(obj)
        elif fmt == "bytes":
            return obj
        elif fmt == "text":
            return obj.encode("utf-8")
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    def _is_dataframe(self, obj: Any) -> bool:
        """Check if object is a DataFrame type."""
        for df_type in get_dataframe_target_types():
            if isinstance(obj, df_type):
                return True
        return False

    def _load_parquet(self, data: bytes, target_type: type[TTarget]) -> TTarget:
        """Load parquet data and convert to target type."""
        import pyarrow.parquet as pq

        table = pq.read_table(io.BytesIO(data))
        return self._narwhals.convert_for_load(table, target_type)

    def _load_csv(self, data: bytes, target_type: type[TTarget]) -> TTarget:
        """Load CSV data and convert to target type."""
        import pyarrow.csv as pcsv

        table = pcsv.read_csv(io.BytesIO(data))
        return self._narwhals.convert_for_load(table, target_type)

    def _load_json(self, data: bytes, target_type: type[TTarget]) -> TTarget:
        """Load JSON data and convert to target type."""
        import json

        if target_type in (dict, list):
            return json.loads(data)

        # For DataFrame types, try to load as records
        import pyarrow.json as pjson

        table = pjson.read_json(io.BytesIO(data))
        return self._narwhals.convert_for_load(table, target_type)

    def _serialize_parquet(self, obj: Any) -> bytes:
        """Serialize DataFrame to parquet bytes."""
        import pyarrow as pa
        import pyarrow.parquet as pq

        # Convert to PyArrow Table if needed
        if not isinstance(obj, pa.Table):
            obj = self._to_arrow_table(obj)

        buf = io.BytesIO()
        pq.write_table(obj, buf)
        return buf.getvalue()

    def _serialize_csv(self, obj: Any) -> bytes:
        """Serialize DataFrame to CSV bytes."""
        import pyarrow as pa
        import pyarrow.csv as pcsv

        # Convert to PyArrow Table if needed
        if not isinstance(obj, pa.Table):
            obj = self._to_arrow_table(obj)

        buf = io.BytesIO()
        pcsv.write_csv(obj, buf)
        return buf.getvalue()

    def _serialize_json(self, obj: Any) -> bytes:
        """Serialize object to JSON bytes."""
        import json

        if isinstance(obj, (dict, list)):
            return json.dumps(obj).encode("utf-8")

        # For DataFrames, convert to records format
        pandas_type = get_pandas_dataframe_type()
        if pandas_type is None:
            raise ImportError("pandas is required for JSON serialization of DataFrames")
        pandas_df = self._narwhals.convert_for_load(obj, pandas_type)
        return pandas_df.to_json(orient="records").encode("utf-8")

    def _to_arrow_table(self, obj: Any) -> Any:
        """Convert DataFrame to PyArrow Table."""
        import pyarrow as pa

        pandas_type = get_pandas_dataframe_type()
        polars_type = get_polars_dataframe_type()

        if pandas_type and isinstance(obj, pandas_type):
            return pa.Table.from_pandas(obj)
        elif polars_type and isinstance(obj, polars_type):
            return obj.to_arrow()
        else:
            raise ValueError(f"Cannot convert {type(obj).__name__} to Arrow Table")

    # Public methods for partition support

    def to_arrow_table(self, obj: Any) -> Any:
        """Convert DataFrame to PyArrow Table (public interface)."""
        return self._to_arrow_table(obj)

    def convert_to_target_type(self, table: Any, target_type: type[TTarget]) -> TTarget:
        """Convert a PyArrow Table to the target DataFrame type."""
        return self._narwhals.convert_for_load(table, target_type)
