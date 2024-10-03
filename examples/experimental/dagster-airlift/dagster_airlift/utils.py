import os
from pathlib import Path
from typing import Optional

DAGSTER_AIRLIFT_PROXIED_STATE_DIR_ENV_VAR = "DAGSTER_AIRLIFT_PROXIED_STATE_DIR"


def get_local_proxied_state_dir() -> Optional[Path]:
    proxied_dir = os.getenv(DAGSTER_AIRLIFT_PROXIED_STATE_DIR_ENV_VAR)
    return Path(proxied_dir) if proxied_dir else None
