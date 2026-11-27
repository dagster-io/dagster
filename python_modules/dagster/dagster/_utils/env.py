import os

from dagster_shared.utils import environ as environ


def using_dagster_dev() -> bool:
    return bool(os.getenv("DAGSTER_IS_DEV_CLI"))


def refresh_local_defs_state_on_load() -> bool:
    """Whether definitions loads in this process should regenerate LOCAL_FILESYSTEM
    defs state (``defs/.local_defs_state``) from current sources instead of serving
    the existing snapshot.

    Set on code server processes spawned in response to a user-initiated code
    location reload (e.g. the "Reload definitions" button in the UI), so that
    reloading definitions also refreshes component state that would otherwise be
    served from a stale snapshot.
    """
    return bool(os.getenv("DAGSTER_REFRESH_LOCAL_DEFS_STATE_ON_LOAD"))


def use_verbose() -> bool:
    return bool(os.getenv("DAGSTER_verbose", "1"))
