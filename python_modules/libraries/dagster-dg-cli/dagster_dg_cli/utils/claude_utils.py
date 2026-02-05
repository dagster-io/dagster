"""Claude Code SDK utilities and availability checking."""


def is_claude_sdk_available() -> bool:
    """Check if Claude Code SDK is available for import.

    Returns:
        True if claude-code-sdk can be imported, False otherwise
    """
    try:
        import claude_code_sdk  # noqa: F401

        return True
    except ImportError:
        return False
