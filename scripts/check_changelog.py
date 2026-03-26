import argparse
import os
import re
import subprocess
import sys


def _get_release_version(change_name: str) -> str:
    return change_name.split(" ")[0]


def _read_changes_from_branch_tip(branch: str) -> str:
    """Fetch the latest from the remote branch and read CHANGES.md from the tip."""
    subprocess.check_call(["git", "fetch", "origin", branch])

    # Compute the git-relative path to CHANGES.md
    repo_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    changes_file = os.path.join(os.path.dirname(__file__), "../CHANGES.md")
    changes_abs = os.path.realpath(changes_file)
    changes_git_path = os.path.relpath(changes_abs, repo_root)

    return subprocess.check_output(
        ["git", "show", f"origin/{branch}:{changes_git_path}"], text=True
    )


def _read_changes_from_local() -> str:
    """Read CHANGES.md from the local checkout."""
    changes_file = os.path.join(os.path.dirname(__file__), "../CHANGES.md")
    with open(changes_file) as f:
        return f.read()


def main(args: list[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="Release version to check for")
    parser.add_argument(
        "--branch",
        help="Fetch and check CHANGES.md from the tip of this remote branch",
    )
    parsed = parser.parse_args(args[1:])

    version = parsed.version.strip()

    if parsed.branch:
        changes = _read_changes_from_branch_tip(parsed.branch)
    else:
        changes = _read_changes_from_local()

    change_entries = re.split(r"\n#+ (\d+\.\d+\.\d+.*)\n", changes)[1:]
    release_name_by_version = {
        _get_release_version(change_entries[i]): change_entries[i].strip()
        for i in range(0, len(change_entries), 2)
    }

    versions_str = "\n  ".join(list(release_name_by_version.keys())[:10])
    assert version in release_name_by_version, (
        f"Version {version} change entries not found in CHANGES.md\n\nFound entries for versions:\n"
        f"  {versions_str}\n  ..."
    )


if __name__ == "__main__":
    main(sys.argv)
