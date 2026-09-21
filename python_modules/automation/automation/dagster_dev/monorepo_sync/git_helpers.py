"""Git helper functions for monorepo sync auditing."""

import re
import subprocess
from pathlib import Path

COMMIT_SEPARATOR = "---COMMIT_BOUNDARY_8f3a1b---"


def git(args: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def extract_label_values(repo_path: Path, label: str) -> dict[str, str]:
    """Parse git log to build {label_value: commit_hash} mapping.

    Searches for commits containing `label: <value>` in their message body.
    Returns a dict mapping label values to the commit hash that contains them.
    Order is newest-first (git log order).
    """
    raw = git(
        [
            "log",
            "--grep",
            f"{label}:",
            f"--format=%H%n%B{COMMIT_SEPARATOR}",
            "master",
        ],
        cwd=repo_path,
    )

    pattern = re.compile(rf"{re.escape(label)}:\s+([0-9a-f]+)")
    result: dict[str, str] = {}

    for raw_chunk in raw.split(COMMIT_SEPARATOR):
        chunk = raw_chunk.strip()
        if not chunk:
            continue

        lines = chunk.split("\n", 1)
        if not lines or len(lines[0]) < 40:
            continue

        commit_hash = lines[0][:40]
        body = lines[1] if len(lines) > 1 else ""

        for match in pattern.finditer(body):
            result[match.group(1)] = commit_hash

    return result


def git_log_hashes(
    repo_path: Path, *, path: str | None = None, since_commit: str | None = None
) -> list[str]:
    """Return commit hashes oldest-first on master.

    If since_commit is provided, only returns commits from that hash onward
    (inclusive) using the `<hash>^..master` range.
    """
    if since_commit:
        args = ["log", "--format=%H", "--reverse", f"{since_commit}^..master"]
    else:
        args = ["log", "--format=%H", "--reverse", "master"]
    if path is not None:
        args.extend(["--", path])
    raw = git(args, cwd=repo_path)
    return [line.strip() for line in raw.strip().splitlines() if line.strip()]


def get_changed_files(repo_path: Path, commit_hash: str) -> set[str] | None:
    """Return the set of files changed in a commit, or None if the commit is not found."""
    try:
        raw = git(
            ["diff-tree", "--no-commit-id", "-r", "--name-only", commit_hash],
            cwd=repo_path,
        )
    except subprocess.CalledProcessError:
        return None
    return {line.strip() for line in raw.strip().splitlines() if line.strip()}


def get_committer_date(repo_path: Path, commit_hash: str) -> str:
    """Return the ISO committer date for sorting (empty string on failure)."""
    try:
        return git(["log", "-1", "--format=%ci", commit_hash], cwd=repo_path).strip()
    except subprocess.CalledProcessError:
        return ""


def get_commit_info(repo_path: Path, commit_hash: str) -> tuple[str, str, str]:
    """Return (committer_date, author, title) for a commit.

    Returns ("", "", "") on failure.
    """
    try:
        raw = git(
            ["log", "-1", "--format=%ci|%an|%s", commit_hash],
            cwd=repo_path,
        )
        parts = raw.strip().split("|", 2)
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
    except subprocess.CalledProcessError:
        pass
    return "", "", ""


def commits_with_label(repo_path: Path, label: str) -> set[str]:
    """Return set of commit hashes that contain the given label in their message."""
    raw = git(
        [
            "log",
            "--grep",
            f"{label}:",
            "--format=%H",
            "master",
        ],
        cwd=repo_path,
    )
    return {line.strip() for line in raw.strip().splitlines() if line.strip()}


def clone_repo(url: str, dest: Path) -> None:
    """Treeless clone of a repo (commit objects only, single branch)."""
    git(
        [
            "clone",
            "--filter=tree:0",
            "--single-branch",
            "--branch",
            "master",
            url,
            str(dest),
        ]
    )
