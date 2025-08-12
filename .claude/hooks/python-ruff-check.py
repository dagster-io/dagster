#!/usr/bin/env python3
import json
import os
import subprocess
import sys


def main():
    """Claude Code hook to run 'make ruff' when Python files are modified."""
    # Read hook input from stdin
    try:
        hook_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error reading hook data: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract file path from the tool use data
    file_path = None
    if "data" in hook_data and "file_path" in hook_data["data"]:
        file_path = hook_data["data"]["file_path"]
    elif "data" in hook_data and "notebook_path" in hook_data["data"]:
        file_path = hook_data["data"]["notebook_path"]

    # Check if a Python file was modified
    if file_path and file_path.endswith(".py"):
        print(f"Python file modified: {file_path}")

        # Change to repository root
        repo_root = os.environ.get("DAGSTER_GIT_REPO_DIR")
        if not repo_root:
            print("DAGSTER_GIT_REPO_DIR not set, using current directory", file=sys.stderr)
            repo_root = os.getcwd()

        try:
            os.chdir(repo_root)
            print("Running make ruff...")

            # Run make ruff
            result = subprocess.run(
                ["make", "ruff"], capture_output=True, text=True, timeout=120, check=False
            )

            if result.returncode == 0:
                print("✓ make ruff completed successfully")
                if result.stdout.strip():
                    print(result.stdout)
            else:
                print(f"⚠ make ruff failed with exit code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                if result.stdout:
                    print(f"Output: {result.stdout}")

        except subprocess.TimeoutExpired:
            print("⚠ make ruff timed out after 120 seconds")
        except FileNotFoundError:
            print("⚠ make command not found")
        except Exception as e:
            print(f"⚠ Error running make ruff: {e}")
    else:
        # Not a Python file, exit silently
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
