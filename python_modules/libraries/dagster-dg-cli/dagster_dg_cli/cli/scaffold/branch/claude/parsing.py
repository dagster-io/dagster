"""Message parsing and validation for Claude CLI responses."""

from dagster_dg_cli.cli.scaffold.branch.validation import (
    ClaudeAssistantMessage,
    ClaudeErrorResult,
    ClaudeSuccessResult,
    ClaudeSystemInit,
    ClaudeUserMessage,
    MCPServer,
    SDKMessage,
)


def parse_sdk_message(data: dict) -> SDKMessage:
    """Parse dict data into SDKMessage using pattern matching on type field."""
    message_type = data.get("type")

    if message_type == "assistant":
        return ClaudeAssistantMessage(
            type=data["type"],
            message=data["message"],
            session_id=data["session_id"],
        )
    elif message_type == "user":
        return ClaudeUserMessage(
            type=data["type"],
            message=data["message"],
            session_id=data["session_id"],
        )
    elif message_type == "result":
        subtype = data["subtype"]
        if subtype == "success":
            return ClaudeSuccessResult(
                type=data["type"],
                subtype=data["subtype"],
                duration_ms=float(data["duration_ms"]),
                duration_api_ms=float(data["duration_api_ms"]),
                is_error=data["is_error"],
                num_turns=data["num_turns"],
                result=data["result"],
                session_id=data["session_id"],
                total_cost_usd=float(data["total_cost_usd"]),
            )
        else:  # error subtypes
            return ClaudeErrorResult(
                type=data["type"],
                subtype=data["subtype"],
                duration_ms=float(data["duration_ms"]),
                duration_api_ms=float(data["duration_api_ms"]),
                is_error=data["is_error"],
                num_turns=data["num_turns"],
                session_id=data["session_id"],
                total_cost_usd=float(data["total_cost_usd"]),
            )
    elif message_type == "system":
        return ClaudeSystemInit(
            type=data["type"],
            subtype=data["subtype"],
            apiKeySource=data["apiKeySource"],
            cwd=data["cwd"],
            session_id=data["session_id"],
            tools=data.get("tools", []),
            mcp_servers=[
                MCPServer(name=server["name"], status=server["status"])
                for server in data.get("mcp_servers", [])
            ],
            model=data["model"],
            permissionMode=data["permissionMode"],
        )
    else:
        raise ValueError(f"Unknown message type: {message_type}")
