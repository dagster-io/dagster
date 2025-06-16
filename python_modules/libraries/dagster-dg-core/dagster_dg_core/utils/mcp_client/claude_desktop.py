from pathlib import Path

from dagster_dg_core.utils import is_macos, is_windows


def get_claude_desktop_config_path() -> Path:
    if is_windows():
        return Path.home() / "AppData" / "Claude" / "claude_desktop_config.json"
    elif is_macos():
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    else:
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"
