import os
from pathlib import Path
from typing import Optional

DAGSTER_AIRLIFT_MIGRATION_STATE_DIR_ENV_VAR = "DAGSTER_AIRLIFT_MIGRATION_STATE_DIR"


def get_local_migration_state_dir() -> Optional[Path]:
    migration_dir = os.getenv(DAGSTER_AIRLIFT_MIGRATION_STATE_DIR_ENV_VAR)
    return Path(migration_dir) if migration_dir else None
