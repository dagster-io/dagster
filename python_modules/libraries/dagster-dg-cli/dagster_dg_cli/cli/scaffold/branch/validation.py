"""Claude Code SDK message types using Dagster @record pattern."""

from typing import Any, Literal, Union

from dagster_shared.record import record

# Claude SDK compatible message models
# Based on SDKMessage type from https://docs.anthropic.com/en/docs/claude-code/sdk as of 2026-08-16
#
# type SDKMessage =
#   // An assistant message
#   | {
#       type: "assistant";
#       message: Message; // from Anthropic SDK
#       session_id: string;
#     }
#
#   // A user message
#   | {
#       type: "user";
#       message: MessageParam; // from Anthropic SDK
#       session_id: string;
#     }
#
#   // Emitted as the last message
#   | {
#       type: "result";
#       subtype: "success";
#       duration_ms: float;
#       duration_api_ms: float;
#       is_error: boolean;
#       num_turns: int;
#       result: string;
#       session_id: string;
#       total_cost_usd: float;
#     }
#
#   // Emitted as the last message, when we've reached the maximum number of turns
#   | {
#       type: "result";
#       subtype: "error_max_turns" | "error_during_execution";
#       duration_ms: float;
#       duration_api_ms: float;
#       is_error: boolean;
#       num_turns: int;
#       session_id: string;
#       total_cost_usd: float;
#     }
#
#   // Emitted as the first message at the start of a conversation
#   | {
#       type: "system";
#       subtype: "init";
#       apiKeySource: string;
#       cwd: string;
#       session_id: string;
#       tools: string[];
#       mcp_servers: {
#         name: string;
#         status: string;
#       }[];
#       model: string;
#       permissionMode: "default" | "acceptEdits" | "bypassPermissions" | "plan";
#     };

ClaudeMessageType = Literal["assistant", "user", "result", "system"]
ClaudeResultSubtype = Literal["success", "error_max_turns", "error_during_execution"]
ClaudeSystemSubtype = Literal["init"]
ClaudePermissionMode = Literal["default", "acceptEdits", "bypassPermissions", "plan"]


@record
class MCPServer:
    """MCP server information."""

    name: str
    status: str


@record
class ClaudeAssistantMessage:
    """Claude assistant message."""

    type: ClaudeMessageType
    message: dict[str, Any]
    session_id: str


@record
class ClaudeUserMessage:
    """Claude user message."""

    type: ClaudeMessageType
    message: dict[str, Any]
    session_id: str


@record
class ClaudeSuccessResult:
    """Claude successful result message."""

    type: ClaudeMessageType
    subtype: ClaudeResultSubtype
    duration_ms: float
    duration_api_ms: float
    is_error: bool
    num_turns: int
    result: str
    session_id: str
    total_cost_usd: float


@record
class ClaudeErrorResult:
    """Claude error result message."""

    type: ClaudeMessageType
    subtype: ClaudeResultSubtype
    duration_ms: float
    duration_api_ms: float
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float


@record
class ClaudeSystemInit:
    """Claude system initialization message."""

    type: ClaudeMessageType
    subtype: ClaudeSystemSubtype
    apiKeySource: str
    cwd: str
    session_id: str
    tools: list[str]
    mcp_servers: list[MCPServer]
    model: str
    permissionMode: ClaudePermissionMode


# Union type for all possible Claude SDK messages
SDKMessage = Union[
    ClaudeAssistantMessage,
    ClaudeUserMessage,
    ClaudeSuccessResult,
    ClaudeErrorResult,
    ClaudeSystemInit,
]
