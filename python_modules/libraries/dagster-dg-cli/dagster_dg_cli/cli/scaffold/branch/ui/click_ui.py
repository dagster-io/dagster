"""Click-based UI implementation for scaffold branch command."""

from typing import Optional

import click

from dagster_dg_cli.utils.ui import daggy_spinner_context

from .interface import ScaffoldUI
from .state import UIState


class ClickScaffoldUI(ScaffoldUI):
    """Click-based UI implementation maintaining current UX."""
    
    def __init__(self, disable_progress: bool = False):
        """Initialize Click UI.
        
        Args:
            disable_progress: Whether to disable progress spinners
        """
        self.disable_progress = disable_progress
        self._active_spinners = {}
        self._last_ui_state = None
        self._rendered_diagnostics = False
    
    def render_state(self, state) -> None:
        """Render current state using Click.
        
        Args:
            state: ScaffoldState containing complete UI state
        """
        # Only render diagnostics info once at the beginning
        if state.diagnostics_enabled and state.diagnostics_path and not self._rendered_diagnostics:
            click.echo(f"🔍 Diagnostics enabled at level - streaming to: {state.diagnostics_path}")
            self._rendered_diagnostics = True
        
        # Render state transitions (only when state changes)
        if state.ui_state != self._last_ui_state:
            if state.ui_state == UIState.PLANNING:
                self._render_planning_start(state)
            elif state.ui_state == UIState.EXECUTING:
                self._render_execution_start(state)
            elif state.ui_state == UIState.COMPLETED:
                self._render_completion(state)
            
            self._last_ui_state = state.ui_state
        
        # Always manage active progress operations
        self._manage_progress_operations(state.progress_operations)
        
        # Render new messages (keep last 5)
        recent_messages = state.messages[-5:] if state.messages else []
        for msg in recent_messages:
            if not hasattr(msg, '_rendered'):  # Avoid re-rendering same message
                self._render_message(msg)
                msg['_rendered'] = True
    
    def _render_planning_start(self, state) -> None:
        """Render planning phase startup."""
        click.echo("🎯 Generating implementation plan...")
        click.echo(f'📋 Request: "{state.prompt[:60]}{"..." if len(state.prompt) > 60 else ""}"')
        
        if state.planning_model:
            click.echo(f"🤖 Planning Model: {state.planning_model} (reasoning-focused for complex planning)")
        if state.project_path:
            click.echo(f"📁 Project: {state.project_path}")
        if state.input_type_name:
            click.echo(f"⚙️  Input Type: {state.input_type_name}")
    
    def _render_execution_start(self, state) -> None:
        """Render execution phase startup."""
        click.echo("\n🚀 Beginning implementation...")
        if state.branch_name:
            click.echo(f"Creating new branch: {state.branch_name}")
    
    def _render_completion(self, state) -> None:
        """Render completion status."""
        if state.pr_url:
            click.echo(f"✅ Successfully created branch and pull request: {state.pr_url}")
        elif state.branch_name:
            click.echo(f"✅ Successfully created branch: {state.branch_name}")
    
    def _manage_progress_operations(self, operations: dict) -> None:
        """Manage active progress operations (spinners)."""
        for op_id, op_data in operations.items():
            if op_data["status"] == "started" and not self.disable_progress:
                if op_id not in self._active_spinners:
                    spinner_ctx = daggy_spinner_context(op_data["name"])
                    self._active_spinners[op_id] = spinner_ctx
                    spinner_ctx.__enter__()
                    
            elif op_data["status"] in ("completed", "failed"):
                if op_id in self._active_spinners:
                    spinner_ctx = self._active_spinners[op_id]
                    spinner_ctx.__exit__(None, None, None)
                    del self._active_spinners[op_id]
    
    def _render_message(self, message: dict) -> None:
        """Render a status message."""
        level = message.get("level", "info")
        msg_text = message.get("message", "")
        
        if level == "success":
            click.echo(f"✅ {msg_text}")
        elif level == "warning":
            click.echo(f"⚠️ {msg_text}")
        elif level == "error":
            click.echo(f"❌ {msg_text}")
        else:  # info
            click.echo(msg_text)
    
    def get_user_input(self, prompt: str, input_type: str = "text") -> str:
        """Get user input with specified prompt."""
        return click.prompt(prompt, type=str)
    
    def get_plan_approval(self, plan_content: str) -> tuple[bool, Optional[str]]:
        """Interactive plan approval matching current UX."""
        click.echo("\n" + "=" * 60)
        click.echo("IMPLEMENTATION PLAN REVIEW")
        click.echo("=" * 60)
        click.echo("")
        
        # Display the plan content directly
        click.echo(plan_content)
        
        click.echo("")
        click.echo("=" * 60)

        while True:
            choice = click.prompt(
                "Plan Review Options:\n"
                "  [a]pprove - Execute this plan as-is\n"
                "  [r]efine - Provide feedback to improve the plan\n"
                "  [c]ancel - Cancel the operation\n\n"
                "Your choice",
                type=click.Choice(["a", "r", "c", "approve", "refine", "cancel"], 
                                 case_sensitive=False),
                default="approve",
            ).lower()

            if choice in ("a", "approve"):
                click.echo("✅ Plan approved! Proceeding with implementation...")
                return True, None
            elif choice in ("r", "refine"):
                feedback = click.prompt(
                    "\nWhat would you like to change about this plan?\n"
                    "Be specific about steps, files, or approaches you'd like modified",
                    type=str,
                )
                click.echo("🔄 Refining plan based on your feedback...")
                return False, feedback
            elif choice in ("c", "cancel"):
                raise click.ClickException("Operation cancelled by user")
    
    def confirm_action(self, message: str) -> bool:
        """Get user confirmation for an action."""
        return click.confirm(message)
    
    def cleanup(self) -> None:
        """Clean up active spinners."""
        for spinner_ctx in self._active_spinners.values():
            try:
                spinner_ctx.__exit__(None, None, None)
            except Exception:
                pass  # Best effort cleanup
        self._active_spinners.clear()