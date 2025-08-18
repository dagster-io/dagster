"""Claude Code SDK utilities and availability checking."""

import sys


def is_claude_sdk_available() -> bool:
    """Check if Claude Code SDK is available for import.

    Returns:
        True if claude-code-sdk can be imported, False otherwise
    """
    if sys.version_info < (3, 10):
        return False

    try:
        import claude_code_sdk  # noqa: F401

        return True
    except ImportError:
        return False


def get_claude_sdk_unavailable_message() -> str:
    """Get a helpful error message when Claude Code SDK is not available.

    Returns:
        Error message with installation instructions
    """
    return (
        "claude_code_sdk is required for AI scaffolding functionality. "
        "Install with: pip install claude-code-sdk>=0.0.19"
    )
