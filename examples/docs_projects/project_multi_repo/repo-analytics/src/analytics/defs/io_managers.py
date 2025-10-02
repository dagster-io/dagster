from pathlib import Path

import dagster as dg
import pandas as pd


@dg.io_manager
def shared_parquet_io_manager(context):
    """Shared I/O manager that writes to a shared temp directory for cross-repository access."""
    shared_dir = Path("/tmp/dagster_shared_assets")
    shared_dir.mkdir(exist_ok=True)

    def _get_path(context):
        shared_dir = Path("/tmp/dagster_shared_assets")
        shared_dir.mkdir(exist_ok=True)
        return shared_dir / f"{context.asset_key.to_user_string()}.parquet"

    def handle_output(context, obj):
        path = _get_path(context)
        if isinstance(obj, pd.DataFrame):
            obj.to_parquet(path, index=False)
            context.log.info(f"Stored asset {context.asset_key} at {path}")
        else:
            # For non-DataFrame objects, use pickle
            import pickle

            pickle_path = shared_dir / f"{context.asset_key.to_user_string()}.pkl"
            with open(pickle_path, "wb") as f:
                pickle.dump(obj, f)
            context.log.info(f"Stored asset {context.asset_key} at {pickle_path}")

    def load_input(context):
        path = _get_path(context)
        if path.exists():
            context.log.info(f"Loading asset {context.asset_key} from {path}")
            return pd.read_parquet(path)
        else:
            # Try pickle format
            import pickle

            shared_dir = Path("/tmp/dagster_shared_assets")
            pickle_path = shared_dir / f"{context.asset_key.to_user_string()}.pkl"
            if pickle_path.exists():
                context.log.info(f"Loading asset {context.asset_key} from {pickle_path}")
                with open(pickle_path, "rb") as f:
                    return pickle.load(f)
            else:
                raise FileNotFoundError(
                    f"Asset {context.asset_key} not found at {path} or {pickle_path}"
                )

    return dg.IOManager(handle_output=handle_output, load_input=load_input)
