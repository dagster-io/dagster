"""State management for scaffold UI reconciliation."""

import copy
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from dagster_shared.record import record


class UIState(Enum):
    """Current UI state for reconciliation."""
    INITIAL = "initial"
    PLANNING = "planning"
    PLAN_REVIEW = "plan_review"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"

@record
class ScaffoldState:
    """Complete state of the scaffold operation for UI reconciliation."""
    ui_state: UIState
    prompt: str = ""
    branch_name: str = ""
    pr_title: str = ""
    pr_url: str = ""
    current_plan: Optional[str] = None
    progress_operations: dict[str, Any] = None
    messages: list[dict] = None
    diagnostics_enabled: bool = False
    diagnostics_path: Optional[str] = None
    errors: list[str] = None
    planning_model: str = ""
    execution_model: str = ""
    input_type_name: str = ""
    project_path: str = ""
    
    def __post_init__(self):
        # Initialize mutable defaults if None
        object.__setattr__(self, 'progress_operations', self.progress_operations or {})
        object.__setattr__(self, 'messages', self.messages or [])
        object.__setattr__(self, 'errors', self.errors or [])

# UI Events for state updates
@record
class ProgressEvent:
    """Progress update event."""
    operation_id: str
    operation_name: str
    status: str  # "started", "progress", "completed", "failed"
    message: str = ""
    progress: Optional[float] = None

@record
class StatusMessage:
    """Status message for user."""
    level: str  # "info", "success", "warning", "error"
    message: str
    timestamp: str
    details: dict[str, Any] = None
    
    def __post_init__(self):
        object.__setattr__(self, 'details', self.details or {})

@record
class DiagnosticsUpdate:
    """Diagnostics system update."""
    enabled: bool
    output_path: Optional[str] = None
    entry_count: int = 0

@record
class PlanUpdate:
    """Plan generation/update event."""
    plan_content: str
    metadata: dict[str, Any] = None
    refinement_count: int = 0
    
    def __post_init__(self):
        object.__setattr__(self, 'metadata', self.metadata or {})

# Union type for all UI events
UIEvent = Union[ProgressEvent, StatusMessage, DiagnosticsUpdate, PlanUpdate]

class ScaffoldStateManager:
    """Manages scaffold state and UI reconciliation."""
    
    def __init__(self, ui):
        """Initialize state manager with UI implementation.
        
        Args:
            ui: ScaffoldUI implementation
        """
        self.ui = ui
        self.state = ScaffoldState(ui_state=UIState.INITIAL)
        self._last_rendered_state = None
    
    def update_state(self, **kwargs) -> None:
        """Update state and trigger UI reconciliation.
        
        Args:
            **kwargs: State fields to update
        """
        # Use record replace to create new state with updates
        from dagster_shared.record import replace
        new_state = replace(self.state, **kwargs)
        self.state = new_state
        self._reconcile_ui()
    
    def emit_event(self, event: UIEvent) -> None:
        """Process an event and update state accordingly.
        
        Args:
            event: UI event to process
        """
        from dagster_shared.record import replace
        
        if isinstance(event, ProgressEvent):
            # Update progress operations
            new_operations = self.state.progress_operations.copy()
            new_operations[event.operation_id] = {
                "name": event.operation_name,
                "status": event.status,
                "message": event.message,
                "progress": event.progress
            }
            self.state = replace(self.state, progress_operations=new_operations)
            
        elif isinstance(event, StatusMessage):
            # Add to messages
            new_messages = self.state.messages.copy()
            new_messages.append({
                "level": event.level,
                "message": event.message,
                "timestamp": event.timestamp,
                "details": event.details
            })
            self.state = replace(self.state, messages=new_messages)
            
        elif isinstance(event, DiagnosticsUpdate):
            # Update diagnostics info
            self.state = replace(
                self.state,
                diagnostics_enabled=event.enabled,
                diagnostics_path=event.output_path
            )
            
        elif isinstance(event, PlanUpdate):
            # Update current plan
            self.state = replace(self.state, current_plan=event.plan_content)
        
        self._reconcile_ui()
    
    def _reconcile_ui(self) -> None:
        """Reconcile UI with current state (only render if changed)."""
        if self._state_changed():
            self.ui.render_state(self.state)
            self._last_rendered_state = copy.deepcopy(self.state)
    
    def _state_changed(self) -> bool:
        """Check if state has changed since last render."""
        return self._last_rendered_state != self.state
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.ui.cleanup()

def create_status_message(level: str, message: str, details: Optional[dict] = None) -> StatusMessage:
    """Helper to create status messages with current timestamp."""
    return StatusMessage(
        level=level,
        message=message,
        timestamp=datetime.now().isoformat(),
        details=details or {}
    )