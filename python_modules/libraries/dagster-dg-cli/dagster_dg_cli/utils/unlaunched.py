"""We hide cli commands that we have not launched yet. Override this by setting
the DG_SHOW_UNLAUNCHED_COMMANDS environment variable to any value.
"""

import os


def show_dg_unlaunched_commands() -> bool:
    """We hide cli commands that we have not launched yet. Override this by setting
    the DG_SHOW_UNLAUNCHED_COMMANDS environment variable to any value.
    """
    return os.getenv("DG_SHOW_UNLAUNCHED_COMMANDS") is not None
