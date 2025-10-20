from typing import Callable
import pickle
import os
import tempfile

from typing import Optional, Any

from dagster_pipes.transforms.transform import (
    TransformResult,
    StorageIOPlugin,
    StorageResult,
    build_transform_inputs,
    invoke_transform,
    TransformMetadata,
)


class FileStorageIO(StorageIOPlugin):
    """StorageIO implementation that stores data in temporary files.

    Uses a well-known temp directory that can be accessed by multiple processes.
    Files are stored as pickle files for serialization.
    """

    def __init__(self, temp_dir: Optional[str] = None):
        if temp_dir is None:
            temp_dir = tempfile.gettempdir()

        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)

    # This is largely copied and pasted from the parent class, but it allows users to completely
    # and totally customize storage behavior include prior to loading inputs and after saving
    # outputs
    def invoke(
        self,
        *,
        transform_fn: Callable[..., TransformResult],
        transform_metadata: TransformMetadata,
    ) -> StorageResult:
        verify_transform_metadata(transform_metadata)

        def load(asset_key: str) -> Any:
            filepath = self._get_filepath(asset_key)
            with open(filepath, "rb") as f:
                return pickle.load(f)

        inputs = build_transform_inputs(transform_fn, load)
        output = invoke_transform(transform_fn, inputs)

        def save(asset_key: str, data: Any) -> None:
            filepath = self._get_filepath(asset_key)
            with open(filepath, "wb") as f:
                pickle.dump(data, f)

        # only supports a single asset right now
        save(transform_metadata.assets[0], output.assets[transform_metadata.assets[0]])
        return StorageResult(output)

    def _get_filepath(self, asset_key: str) -> str:
        safe_key = asset_key.replace("/", "_")
        return os.path.join(self.temp_dir, f"{safe_key}.pkl")


def verify_transform_metadata(transform_metadata: TransformMetadata) -> None:
    if len(transform_metadata.assets) != 1:
        raise ValueError(
            f"Transform {transform_metadata.transform_fn.__name__} must produce exactly one asset. "
            f"Got {len(transform_metadata.assets)} assets: {transform_metadata.assets}"
        )
    if len(transform_metadata.checks) != 0:
        raise ValueError(
            f"Transform {transform_metadata.transform_fn.__name__} must not produce any checks. "
            f"Got {len(transform_metadata.checks)} checks: {transform_metadata.checks}"
        )
