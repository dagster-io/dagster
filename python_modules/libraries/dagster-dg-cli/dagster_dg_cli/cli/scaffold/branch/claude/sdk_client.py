"""Claude Code SDK integration for branch scaffolding operations."""

from datetime import datetime
from time import perf_counter
from typing import Any, Optional, Protocol

from claude_code_sdk import query
from claude_code_sdk.types import (
    AssistantMessage,
    ClaudeCodeOptions,
    Message,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from dagster_dg_cli.cli.scaffold.branch.claude.diagnostics import AIInteraction, ClaudeDiagnostics


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


class ClaudeSDKClient:
    """Claude Code SDK integration with diagnostics and output streaming."""

    def __init__(self, diagnostics: ClaudeDiagnostics):
        """Initialize the Claude SDK client.

        Args:
            diagnostics: Diagnostics service for logging
        """
        self.diagnostics = diagnostics
        self.total_cost_usd = 0.0
        self.total_tokens = 0
        self.conversation_history: list[Message] = []

    async def scaffold_with_streaming(
        self,
        prompt: str,
        allowed_tools: list[str],
        output_channel: OutputChannel,
        disallowed_tools: Optional[list[str]] = None,
        verbose: bool = False,
    ) -> list[Message]:
        """Execute scaffolding operation with Claude Code SDK.

        Args:
            prompt: The prompt to send to Claude
            allowed_tools: List of tool names that Claude is allowed to use
            output_channel: Channel to stream output to
            disallowed_tools: List of tool names that Claude is NOT allowed to use (ignored in SDK)
            verbose: If True, display raw message data instead of formatted output

        Returns:
            List of SDK message objects

        Raises:
            Exception: If the SDK operation fails
        """
        collected_messages: list[Message] = []

        with self.diagnostics.claude_operation(
            operation_name="claude_sdk_scaffold",
            error_code="claude_sdk_scaffold_failed",
            error_message="Claude SDK scaffolding operation failed",
            prompt_length=len(prompt),
        ):
            start_time = perf_counter()

            # Configure SDK options
            options = ClaudeCodeOptions(
                allowed_tools=allowed_tools,
                permission_mode="acceptEdits",  # Auto-accept file edits for scaffolding
                max_turns=20,  # Match existing MAX_TURNS
            )

            # Execute SDK query with streaming
            async for message in query(prompt=prompt, options=options):
                # Collect SDK message objects directly
                collected_messages.append(message)

                # Stream output to channel
                if verbose:
                    debug_output = self._format_message_for_debug(message)
                    output_channel.write(debug_output)
                else:
                    # Format message for user-friendly output
                    formatted_output = self._format_message_for_output(message)
                    if formatted_output:
                        output_channel.write(formatted_output)

            duration_ms = (perf_counter() - start_time) * 1000

            # Update usage statistics from result messages
            self._update_usage_stats(collected_messages)

            # Log the interaction
            interaction = AIInteraction(
                correlation_id=self.diagnostics.correlation_id,
                timestamp=datetime.now().isoformat(),
                prompt=prompt,
                response=f"[SDK_STREAMED: {len(collected_messages)} messages]",
                token_count=self.total_tokens,
                tools_used=allowed_tools,
                duration_ms=duration_ms,
            )
            self.diagnostics.log_ai_interaction(interaction)

            return collected_messages

    def _format_content_blocks(self, blocks: list) -> list[str]:
        """Format content blocks into debug strings.

        Args:
            blocks: List of content blocks to format

        Returns:
            List of formatted block descriptions
        """
        content_blocks = []
        for block in blocks:
            if isinstance(block, TextBlock):
                content_blocks.append(f"TextBlock({block.text!r})")
            elif isinstance(block, ToolUseBlock):
                content_blocks.append(f"ToolUseBlock(name={block.name!r}, id={block.id!r})")
            elif isinstance(block, ToolResultBlock):
                content_blocks.append(
                    f"ToolResultBlock(tool_use_id={block.tool_use_id!r}, is_error={block.is_error})"
                )
            elif isinstance(block, ThinkingBlock):
                content_blocks.append(f"ThinkingBlock({block.thinking!r})")
            else:
                content_blocks.append(f"{type(block).__name__}")
        return content_blocks

    def _format_message_for_debug(self, message: Message) -> str:
        """Format SDK message for debug output.

        Args:
            message: SDK message object

        Returns:
            Debug string representation
        """
        message_type = type(message).__name__

        # Handle different SDK message types with specific debug formatting
        if isinstance(message, AssistantMessage):
            content_blocks = self._format_content_blocks(message.content)
            content_summary = f" content=[{', '.join(content_blocks)}]"
            return f"[DEBUG] {message_type} model={message.model!r}{content_summary}\n"

        elif isinstance(message, SystemMessage):
            system_info = f" subtype={message.subtype!r}"
            if "cwd" in message.data:
                system_info += f" cwd={message.data['cwd']!r}"
            if "model" in message.data:
                system_info += f" model={message.data['model']!r}"
            if "permissionMode" in message.data:
                system_info += f" permissionMode={message.data['permissionMode']!r}"
            if message.data.get("tools"):
                tools = message.data["tools"]
                tools_preview = f"{len(tools)} tools" + (
                    f" ({', '.join(tools[:3])}...)" if len(tools) > 3 else f" ({', '.join(tools)})"
                )
                system_info += f" tools=[{tools_preview}]"
            return f"[DEBUG] {message_type}{system_info}\n"

        elif isinstance(message, UserMessage):
            if isinstance(message.content, str):
                user_info = f" content={message.content!r}"
            else:
                content_blocks = self._format_content_blocks(message.content)
                user_info = f" content=[{', '.join(content_blocks)}]"
            return f"[DEBUG] {message_type}{user_info}\n"

        elif isinstance(message, ResultMessage):
            result_info = f" subtype={message.subtype!r} duration_ms={message.duration_ms} num_turns={message.num_turns}"
            if message.total_cost_usd is not None:
                result_info += f" cost_usd={message.total_cost_usd:.4f}"
            if message.result:
                result_info += f" result={message.result!r}"
            return f"[DEBUG] {message_type}{result_info}\n"

        else:
            # Generic fallback for unknown message types
            return f"[DEBUG] {message_type} - {message!r}\n"

    def _format_message_for_output(self, message: Message) -> Optional[str]:
        """Format SDK message for user-friendly output.

        Args:
            message: SDK message object

        Returns:
            Formatted string for output, or None if no output needed
        """
        if isinstance(message, AssistantMessage):
            # Extract text content from assistant messages
            for block in message.content:
                if isinstance(block, TextBlock):
                    return block.text + "\n"
            return None
        elif isinstance(message, ResultMessage):
            # Show result information
            if message.result:
                return f"✅ Operation completed: {message.result}\n"
            return "✅ Operation completed\n"
        else:
            # For other message types, return nothing to avoid noise
            return None

    def _update_usage_stats(self, messages: list[Message]) -> None:
        """Update usage statistics from collected messages.

        Args:
            messages: List of SDK message objects to extract stats from
        """
        for message in messages:
            # Only process ResultMessage instances
            if not isinstance(message, ResultMessage):
                continue

            if message.total_cost_usd is None:
                continue

            cost = message.total_cost_usd
            if cost > self.total_cost_usd:
                self.total_cost_usd = cost

            self.diagnostics.debug(
                category="claude_sdk_usage_update",
                message="Updated SDK usage statistics",
                data={
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
            "sdk_version": "claude-code-sdk",
        }
