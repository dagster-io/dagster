"""Dagster definitions entry point for this project."""

import os
import time
from pathlib import Path

from dagster import Definitions, definitions, load_from_defs_folder

# Enable remote debugging when DAGSTER_DEBUG is set.
if os.environ.get("DAGSTER_DEBUG"):
    try:
        import debugpy
    except ImportError:
        print("debugpy not installed — install it with your dev tooling.")
        debugpy = None  # type: ignore[assignment]

    if debugpy is not None:
        try:
            debugpy.listen(("localhost", 5678))
            print("debugpy listening on port 5678 — attach your IDE debugger")
        except RuntimeError:
            # Subprocess: pause briefly so debugpy can sync breakpoints from VS Code
            debugpy.trace_this_thread(True)
            time.sleep(0.5)


@definitions
def defs() -> Definitions:
    """Load all Dagster definitions from the defs/ folder."""
    return load_from_defs_folder(path_within_project=Path(__file__).parent)
