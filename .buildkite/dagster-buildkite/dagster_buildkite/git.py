import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set


def get_commit(rev):
    return (
        subprocess.check_output(["git", "rev-parse", "--short", rev])
        .decode("utf-8")
        .strip()
    )


def get_commit_message(rev):
    return (
        subprocess.check_output(
            ["git", "rev-list", "--format=%B", "--max-count=1", rev]
        )
        .decode("utf-8")
        .strip()
    )


@dataclass
class GitInfo:
    directory: Path
    base_branch: Optional[str] = "master"


class ChangedFiles:
    _repositories: Set[Path] = set()
    all: Set[Path] = set()

    @classmethod
    def load_from_git(cls, git_info: GitInfo) -> None:
        # Only do the expensive git diffing once
        if git_info.directory in cls._repositories:
            return None

        original_directory = os.getcwd()
        os.chdir(git_info.directory)

        subprocess.call(["git", "fetch", "origin", str(git_info.base_branch)])
        origin = get_commit(f"origin/{git_info.base_branch}")
        head = get_commit("HEAD")
        logging.info(
            f"Changed files between origin/{git_info.base_branch} ({origin}) and HEAD ({head}):"
        )
        paths = (
            subprocess.check_output(
                [
                    "git",
                    "diff",
                    f"origin/{git_info.base_branch}...HEAD",
                    "--name-only",
                ]
            )
            .decode("utf-8")
            .strip()
            .split("\n")
        )
        for path in sorted(paths):
            logging.info("  - " + path)
            cls.all.add(git_info.directory / path)

        os.chdir(original_directory)
