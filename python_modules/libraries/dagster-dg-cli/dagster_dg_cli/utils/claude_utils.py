"""Claude Agent SDK utilities and availability checking."""

import sys


def is_claude_sdk_available() -> bool:
    """Check if Claude Agent SDK is available for import.

    Returns:
        True if claude-agent-sdk can be imported, False otherwise
    """
    if sys.version_info < (3, 10):
        return False

    try:
        import claude_agent_sdk  # noqa: F401

        return True
    except ImportError:
        return False
