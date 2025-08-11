"""We hide cli commands that we have not shipped yet. Override this by setting
the DG_SHOW_HIDDEN_COMMANDS environment variable to any value.
"""

import os


def show_dg_hidden_commands() -> bool:
    """We hide cli commands that we have not shipped yet. Override this by setting
    the DG_SHOW_HIDDEN_COMMANDS environment variable to any value.
    """
    return os.getenv("DG_SHOW_HIDDEN_COMMANDS") is not None
