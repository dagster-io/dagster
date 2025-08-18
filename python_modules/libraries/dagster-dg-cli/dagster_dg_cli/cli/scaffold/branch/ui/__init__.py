"""UI abstraction layer for scaffold branch command."""

from .click_ui import ClickScaffoldUI
from .interface import ScaffoldUI
from .state import (
    DiagnosticsUpdate,
    PlanUpdate,
    ProgressEvent,
    ScaffoldState,
    ScaffoldStateManager,
    StatusMessage,
    UIState,
    create_status_message,
)

__all__ = [
    "ClickScaffoldUI",
    "DiagnosticsUpdate",
    "PlanUpdate",
    "ProgressEvent",
    "ScaffoldState",
    "ScaffoldStateManager",
    "ScaffoldUI",
    "StatusMessage",
    "UIState",
    "create_status_message"
]