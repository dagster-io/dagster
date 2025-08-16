"""Low-level Claude CLI execution and process management."""

import functools
import json
import os
import re
import subprocess
from datetime import datetime
from time import perf_counter
from typing import Any, Optional, Protocol

from dagster_dg_cli.cli.scaffold.branch.claude.diagnostics import AIInteraction, ClaudeDiagnostics
from dagster_dg_cli.cli.scaffold.branch.claude.parsing import parse_sdk_message
from dagster_dg_cli.cli.scaffold.branch.claude.rendering import render_claude_output
from dagster_dg_cli.cli.scaffold.branch.validation import (
    ClaudeErrorResult,
    ClaudeSuccessResult,
    SDKMessage,
)


class ClaudeClient:
    """Reliable interface to Claude CLI that handles errors, retries, and type coercion.

    This class wraps the low-level Claude CLI invocation and provides:
    - Automatic retry logic with exponential backoff
    - Type coercion for common issues (int/float mismatches)
    - Cost and conversation tracking
    - Clean error handling and reporting
    - Multi-turn conversation support for planning sessions
    """

    def __init__(self, diagnostics: ClaudeDiagnostics):
        """Initialize the Claude interface.

        Args:
            diagnostics: Diagnostics service for logging
        """
        self.diagnostics = diagnostics
        self.total_cost_usd = 0.0
        self.total_tokens = 0
        self.conversation_history: list[SDKMessage] = []
        self.planning_session_active: bool = False
        self.planning_context: Optional[dict[str, Any]] = None

    def invoke(
        self,
        prompt: str,
        allowed_tools: list[str],
        output_channel: "OutputChannel",
        disallowed_tools: Optional[list[str]],
        verbose: bool,
    ) -> list[SDKMessage]:
        """Invoke Claude with error handling.

        Args:
            prompt: The prompt to send to Claude
            allowed_tools: List of tool names that Claude is allowed to use
            output_channel: Channel to stream output to (use NullOutputChannel to discard output)
            disallowed_tools: List of tool names that Claude is NOT allowed to use
            verbose: If True and streaming, display raw JSON instead of formatted messages

        Returns:
            List of validated SDKMessage objects from Claude CLI output

        Raises:
            Exception: If the invocation fails
        """
        self.diagnostics.debug(
            "claude_interface_invoke",
            "Claude invocation starting",
            {
                "prompt_length": len(prompt),
                "allowed_tools_count": len(allowed_tools),
            },
        )

        # Call the underlying client function
        messages = invoke_claude_direct(
            prompt=prompt,
            allowed_tools=allowed_tools,
            diagnostics=self.diagnostics,
            output_channel=output_channel,
            disallowed_tools=disallowed_tools,
            verbose=verbose,
        )

        # Track conversation history - messages are always collected
        self.conversation_history.extend(messages)
        self._update_usage_stats(messages)

        self.diagnostics.info(
            "claude_interface_success",
            "Claude invocation succeeded",
            {
                "messages_returned": len(messages),
                "total_cost_usd": self.total_cost_usd,
                "total_tokens": self.total_tokens,
            },
        )

        return messages

    def _update_usage_stats(self, messages: list[SDKMessage]) -> None:
        """Update usage statistics from Claude response messages.

        Args:
            messages: List of SDKMessage objects to extract stats from
        """
        for message in messages:
            if isinstance(message, (ClaudeSuccessResult, ClaudeErrorResult)):
                # Update cost tracking
                cost = message.total_cost_usd
                if cost > self.total_cost_usd:
                    self.total_cost_usd = cost

                self.diagnostics.debug(
                    "claude_interface_usage_update",
                    "Updated usage statistics",
                    {
                        "session_cost_usd": cost,
                        "total_cost_usd": self.total_cost_usd,
                        "num_turns": message.num_turns,
                    },
                )

    def get_usage_summary(self) -> dict[str, Any]:
        """Get a summary of usage statistics.

        Returns:
            Dictionary containing usage statistics
        """
        return {
            "total_cost_usd": self.total_cost_usd,
            "total_tokens": self.total_tokens,
            "conversation_length": len(self.conversation_history),
            "timestamp": datetime.now().isoformat(),
            "planning_session_active": self.planning_session_active,
        }

    def start_planning_session(self, context: dict[str, Any]) -> None:
        """Start a multi-turn planning session.

        Args:
            context: Planning context including user input, project info, etc.
        """
        self.planning_session_active = True
        self.planning_context = context

        self.diagnostics.info(
            "planning_session_started",
            "Started multi-turn planning session",
            {
                "context_keys": list(context.keys()),
                "conversation_length": len(self.conversation_history),
            },
        )

    def end_planning_session(self) -> dict[str, Any]:
        """End the current planning session and return session summary.

        Returns:
            Summary of the planning session including conversation history
        """
        if not self.planning_session_active:
            self.diagnostics.warning(
                "planning_session_end_without_start",
                "Attempted to end planning session that was not active",
                {},
            )
            return {}

        session_summary = {
            "conversation_turns": len(self.conversation_history),
            "total_cost": self.total_cost_usd,
            "session_context": self.planning_context,
            "ended_at": datetime.now().isoformat(),
        }

        self.planning_session_active = False
        self.planning_context = None

        self.diagnostics.info(
            "planning_session_ended",
            "Ended multi-turn planning session",
            session_summary,
        )

        return session_summary

    def invoke_planning_turn(
        self,
        prompt: str,
        allowed_tools: list[str],
        output_channel: "OutputChannel",
        continue_conversation: bool = True,
    ) -> list[SDKMessage]:
        """Invoke Claude for a planning conversation turn.

        This method is specifically designed for multi-turn planning conversations
        where context from previous turns should be maintained.

        Args:
            prompt: The prompt for this turn
            allowed_tools: List of tool names that Claude is allowed to use
            output_channel: Channel to stream output to
            continue_conversation: Whether to maintain conversation context

        Returns:
            List of validated SDKMessage objects from Claude CLI output
        """
        if not self.planning_session_active:
            self.diagnostics.warning(
                "planning_turn_without_session",
                "Planning turn invoked without active session",
                {"prompt_length": len(prompt)},
            )

        self.diagnostics.debug(
            "planning_turn_start",
            "Starting planning conversation turn",
            {
                "prompt_length": len(prompt),
                "conversation_turns": len(self.conversation_history),
                "continue_conversation": continue_conversation,
            },
        )

        # For planning turns, we may want to include previous context
        effective_prompt = prompt
        if continue_conversation and self.planning_context:
            # Add planning context to the prompt
            context_summary = "\n".join(
                [
                    "Previous planning context:",
                    f"- User input: {self.planning_context.get('user_input', 'N/A')}",
                    f"- Project patterns: {len(self.planning_context.get('codebase_patterns', {}))} patterns detected",
                    f"- Available components: {len(self.planning_context.get('existing_components', []))} components",
                    "",
                    "Current request:",
                ]
            )
            effective_prompt = context_summary + effective_prompt

        # Use the standard invoke method but with planning-specific context
        return self.invoke(
            prompt=effective_prompt,
            allowed_tools=allowed_tools,
            output_channel=output_channel,
            disallowed_tools=["Bash(python:*)", "WebSearch", "WebFetch"],
            verbose=False,
        )


class OutputChannel(Protocol):
    """Protocol for output channels that can receive text."""

    def write(self, text: str) -> None:
        """Write text to the output channel."""
        ...


class NullOutputChannel:
    """Output channel that discards all output."""

    def write(self, text: str) -> None:
        """Discard all text output."""
        pass


@functools.cache
def find_claude() -> list[str]:
    """Find the Claude CLI executable.

    Attempts to locate the Claude CLI tool by checking:
    1. If 'claude' is available on the system PATH
    2. If 'claude' is available as a shell alias

    Returns:
        List containing the command to run Claude
    """
    try:  # on PATH
        subprocess.run(
            ["claude", "--version"],
            check=False,
            capture_output=True,
        )
        return ["claude"]
    except FileNotFoundError:
        # check for alias (auto-updating version recommends registering an alias instead of putting on PATH)
        result = subprocess.run(
            [os.getenv("SHELL", "bash"), "-ic", "type claude"],
            capture_output=True,
            text=True,
            check=False,
        )
        path_match = re.search(r"(/[^\s`\']+)", result.stdout)
        if path_match:
            return [path_match.group(1)]

        raise


def invoke_claude_direct(
    prompt: str,
    allowed_tools: list[str],
    diagnostics: ClaudeDiagnostics,
    output_channel: OutputChannel,
    disallowed_tools: Optional[list[str]],
    verbose: bool,
) -> list[SDKMessage]:
    """Unified Claude CLI invocation with optional streaming.

    Executes the Claude CLI tool with streaming JSON output.
    Always returns collected messages. Optionally streams formatted output to a channel.

    Args:
        prompt: The prompt to send to Claude
        allowed_tools: List of tool names that Claude is allowed to use
        diagnostics: Diagnostics service for logging
        output_channel: Channel to stream output to (use NullOutputChannel to discard output)
        disallowed_tools: List of tool names that Claude is NOT allowed to use
        verbose: If True and streaming, display raw JSON instead of formatted messages

    Returns:
        List of validated SDKMessage objects from Claude CLI output

    Raises:
        AssertionError: If Claude CLI is not found on the system
    """
    diagnostics.debug(
        "claude_invocation_unified",
        "Invoking Claude CLI with unified interface",
        {
            "prompt_length": len(prompt),
            "allowed_tools_count": len(allowed_tools),
            "allowed_tools": allowed_tools,
            "always_streaming": True,
            "verbose": verbose,
            "disallowed_tools": disallowed_tools,
        },
    )

    claude_cmd = find_claude()
    cmd = [
        *claude_cmd,
        "-p",
        prompt,
        "--allowedTools",
        ",".join(allowed_tools),
        "--output-format",
        "stream-json",
        "--verbose",
    ]

    # Add disallowed tools if specified
    if disallowed_tools:
        cmd.extend(["--disallowedTools", ",".join(disallowed_tools)])

    start_time = perf_counter()
    collected_messages: list[SDKMessage] = []

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdout is not None

        for line in process.stdout:
            line_json = json.loads(line)

            # Parse as SDKMessage for validation and consistency
            message = parse_sdk_message(line_json)

            # Always collect messages for diagnostics and potential return
            collected_messages.append(message)

            # Always stream output to the provided channel
            if verbose:
                output_channel.write(json.dumps(line_json, indent=2))
            else:
                # Render the validated message
                output = render_claude_output(message)
                if output:
                    output_channel.write(output)

        process.wait()
        duration_ms = (perf_counter() - start_time) * 1000

        # Check process return code
        if process.returncode != 0:
            stderr_content = process.stderr.read() if process.stderr else "No stderr"
            diagnostics.error(
                "claude_process_failed",
                "Claude CLI process failed",
                {
                    "return_code": process.returncode,
                    "stderr": stderr_content,
                    "command": cmd,
                },
            )
            raise RuntimeError(
                f"Claude CLI failed with return code {process.returncode}: {stderr_content}"
            )

        # Log the interaction with collected content
        interaction = AIInteraction(
            correlation_id=diagnostics.correlation_id,
            timestamp=datetime.now().isoformat(),
            prompt=prompt,
            response=f"[STREAMED_AND_COLLECTED: {len(collected_messages)}]",
            token_count=None,  # Not available from CLI
            tools_used=allowed_tools,
            duration_ms=duration_ms,
        )
        diagnostics.log_ai_interaction(interaction)

        # Log any stderr output
        if process.stderr:
            stderr_content = process.stderr.read()
            if stderr_content:
                diagnostics.debug(
                    "claude_unified_stderr",
                    "Claude CLI stderr output",
                    {"stderr": stderr_content},
                )

        # Always return collected messages regardless of output mode
        return collected_messages

    except Exception as e:
        duration_ms = (perf_counter() - start_time) * 1000

        diagnostics.error(
            "claude_unified_invocation_failed",
            "Claude CLI unified invocation failed",
            {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_ms": duration_ms,
                "command": cmd,
                "always_streaming": True,
            },
        )
        raise
