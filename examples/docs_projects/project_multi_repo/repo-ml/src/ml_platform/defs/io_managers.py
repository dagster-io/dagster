"""Shared IO managers for cross-code-location asset dependencies."""

import os
import pickle
from pathlib import Path

import pandas as pd
from dagster import InputContext, IOManager, OutputContext, io_manager


class SharedFileIOManager(IOManager):
    """File-based IO manager that stores assets in a shared location accessible by both code locations."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, context) -> Path:
        """Generate file path for the asset."""
        asset_key = context.asset_key.path[-1]  # Get the last part of the asset key
        return self.base_path / f"{asset_key}.parquet"

    def handle_output(self, context: OutputContext, obj):
        """Store the asset output."""
        path = self._get_path(context)

        if isinstance(obj, pd.DataFrame):
            obj.to_parquet(path)
            context.log.info(f"Stored DataFrame at {path}")
        else:
            # Fallback to pickle for other types
            with open(path.with_suffix(".pkl"), "wb") as f:
                pickle.dump(obj, f)
            context.log.info(f"Stored object at {path.with_suffix('.pkl')}")

    def load_input(self, context: InputContext):
        """Load the asset input."""
        path = self._get_path(context)

        # Try parquet first (for DataFrames)
        if path.exists():
            context.log.info(f"Loading DataFrame from {path}")
            return pd.read_parquet(path)

        # Fallback to pickle
        pickle_path = path.with_suffix(".pkl")
        if pickle_path.exists():
            context.log.info(f"Loading object from {pickle_path}")
            with open(pickle_path, "rb") as f:
                return pickle.load(f)

        raise FileNotFoundError(f"Could not find asset file at {path} or {pickle_path}")


@io_manager
def shared_file_io_manager(init_context):
    """IO manager that stores assets in a shared file system location."""
    # Use a shared directory that both code locations can access
    base_path = os.getenv("SHARED_ASSETS_PATH", "/tmp/dagster_shared_assets")
    return SharedFileIOManager(base_path)
