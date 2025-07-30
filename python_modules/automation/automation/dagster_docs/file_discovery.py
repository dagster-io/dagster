"""File discovery functions for finding changed files."""

import subprocess
from pathlib import Path
from typing import Union


def git_changed_files(root_path: Path) -> list[Path]:
    """Get list of Python files with uncommitted changes using git.

    Uses 'git diff --name-only HEAD' to find both staged and unstaged changes.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=root_path,
        )

        files = []
        for line in result.stdout.strip().split("\n"):
            if line and line.endswith(".py"):
                file_path = root_path / line
                if file_path.exists():
                    files.append(file_path)

        return files
    except subprocess.CalledProcessError:
        # Return empty list if git command fails
        return []


def git_staged_files(root_path: Path) -> list[Path]:
    """Get list of Python files with staged changes using git.

    Uses 'git diff --cached --name-only' to find only staged changes.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
            cwd=root_path,
        )

        files = []
        for line in result.stdout.strip().split("\n"):
            if line and line.endswith(".py"):
                file_path = root_path / line
                if file_path.exists():
                    files.append(file_path)

        return files
    except subprocess.CalledProcessError:
        # Return empty list if git command fails
        return []


def git_diff_files(root_path: Path, base_ref: str = "HEAD") -> list[Path]:
    """Get list of Python files that differ from a git reference.

    Args:
        root_path: Root directory of the git repository
        base_ref: Git reference to compare against (default: HEAD)
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_ref],
            capture_output=True,
            text=True,
            check=True,
            cwd=root_path,
        )

        files = []
        for line in result.stdout.strip().split("\n"):
            if line and line.endswith(".py"):
                file_path = root_path / line
                if file_path.exists():
                    files.append(file_path)

        return files
    except subprocess.CalledProcessError:
        # Return empty list if git command fails
        return []


def explicit_files(file_list: list[Path]) -> list[Path]:
    """Return an explicit list of files.

    Useful for testing or when you have a predetermined list of files to validate.
    Filters out non-existent files.
    """
    return [f for f in file_list if f.exists()]


def glob_files(root_path: Path, pattern: str) -> list[Path]:
    """Find files matching a glob pattern.

    Args:
        root_path: Root directory to search from
        pattern: Glob pattern (e.g., "**/*.py", "src/**/*.py")
    """
    return list(root_path.glob(pattern))


def recursive_python_files(
    root_path: Path, exclude_patterns: Union[list[str], None] = None
) -> list[Path]:
    """Find all Python files recursively in a directory.

    Args:
        root_path: Root directory to search
        exclude_patterns: List of patterns to exclude (e.g., ["test_*", "*_test.py"])
    """
    if exclude_patterns is None:
        exclude_patterns = []

    files = []
    for py_file in root_path.rglob("*.py"):
        # Check if file matches any exclude pattern
        should_exclude = False
        for pattern in exclude_patterns:
            if py_file.match(pattern):
                should_exclude = True
                break

        if not should_exclude:
            files.append(py_file)

    return files
