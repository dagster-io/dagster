from collections.abc import Mapping
from enum import Enum
from typing import TYPE_CHECKING

import packaging.version

if TYPE_CHECKING:
    from dagster._core.workspace.workspace import CodeLocationEntry


class CodeLocationFeatureFlags(Enum):
    SHOW_SINGLE_RUN_BACKFILL_TOGGLE = "SHOW_SINGLE_RUN_BACKFILL_TOGGLE"


def get_feature_flags_for_location(
    code_location_entry: "CodeLocationEntry",
) -> Mapping[CodeLocationFeatureFlags, bool]:
    return {
        CodeLocationFeatureFlags.SHOW_SINGLE_RUN_BACKFILL_TOGGLE: (
            get_should_show_single_run_backfill_toggle(code_location_entry)
        )
    }


def get_should_show_single_run_backfill_toggle(code_location_entry: "CodeLocationEntry"):
    # Starting in version 1.5 we stopped showing the single-run backfill toggle in the UI -
    # instead it is now set in code

    if not code_location_entry.code_location:
        # Error or loading status
        return False

    dagster_library_version = (
        code_location_entry.code_location.get_dagster_library_versions() or {}
    ).get("dagster")

    if not dagster_library_version:
        # Old enough version that it wasn't being stored
        return True

    if dagster_library_version == "1!0+dev":
        return False

    try:
        version = packaging.version.parse(dagster_library_version)
        return version.major < 1 or (version.major == 1 and version.minor < 5)
    except packaging.version.InvalidVersion:
        return False
