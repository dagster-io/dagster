#!/usr/bin/env python3
import json
import os
import subprocess
import sys


def _make_me_click_echo(msg: str, *, err: bool = False) -> None:
    """Print function for CLI output - centralized to suppress T201 warnings."""
    print(msg, file=sys.stderr if err else sys.stdout)


def main():
    """Claude Code hook to run 'make ruff' when Python files are modified."""
    # Read hook input from stdin
    try:
        hook_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception) as e:
        _make_me_click_echo(f"Error reading hook data: {e}", err=True)
        sys.exit(1)

    # Extract file path from the tool use data
    file_path = None
    if "data" in hook_data and "file_path" in hook_data["data"]:
        file_path = hook_data["data"]["file_path"]
    elif "data" in hook_data and "notebook_path" in hook_data["data"]:
        file_path = hook_data["data"]["notebook_path"]

    # Check if a Python file was modified
    if file_path and file_path.endswith(".py"):
        _make_me_click_echo(f"Python file modified: {file_path}")

        # Use current working directory
        repo_root = os.getcwd()

        try:
            os.chdir(repo_root)
            _make_me_click_echo("Running make ruff...")

            # Run make ruff
            result = subprocess.run(
                ["make", "ruff"], capture_output=True, text=True, timeout=120, check=False
            )

            if result.returncode == 0:
                _make_me_click_echo("✓ make ruff completed successfully")
                if result.stdout.strip():
                    _make_me_click_echo(result.stdout)
            else:
                _make_me_click_echo(f"⚠ make ruff failed with exit code {result.returncode}")
                if result.stderr:
                    _make_me_click_echo(f"Error: {result.stderr}")
                if result.stdout:
                    _make_me_click_echo(f"Output: {result.stdout}")

        except subprocess.TimeoutExpired:
            _make_me_click_echo("⚠ make ruff timed out after 120 seconds")
        except FileNotFoundError:
            _make_me_click_echo("⚠ make command not found")
        except Exception as e:
            _make_me_click_echo(f"⚠ Error running make ruff: {e}")
    else:
        # Not a Python file, exit silently
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
