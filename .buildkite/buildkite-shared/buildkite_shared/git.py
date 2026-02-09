import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def get_commit(rev):
    return subprocess.check_output(["git", "rev-parse", "--short", rev]).decode("utf-8").strip()


def get_commit_message(rev):
    return (
        subprocess.check_output(["git", "rev-list", "--format=%B", "--max-count=1", rev])
        .decode("utf-8")
        .strip()
    )


@dataclass
class GitInfo:
    directory: Path
    base_branch: Optional[str] = "master"


class ChangedFiles:
    _repositories: set[Path] = set()
    all: set[Path] = set()

    @classmethod
    def load_from_git(cls, git_info: GitInfo) -> None:
        # Only do the expensive git diffing once
        if git_info.directory in cls._repositories:
            return None

        original_directory = os.getcwd()
        logging.info(
            f"ChangedFiles.load_from_git: original_directory={original_directory}, git_info.directory={git_info.directory}"
        )
        os.chdir(git_info.directory)
        logging.info(f"ChangedFiles.load_from_git: after chdir, cwd={os.getcwd()}")

        # Mark current directory as safe (needed when running from internal repo's dagster-oss/)
        subprocess.call(["git", "config", "--global", "--add", "safe.directory", os.getcwd()])

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
                    "--relative",  # Paths relative to cwd
                    "--",
                    ".",  # Only files in current directory
                ]
            )
            .decode("utf-8")
            .strip()
            .split("\n")
        )
        for path in sorted(paths):
            if path:
                logging.info("  - " + path)
                cls.all.add(Path(path))

        os.chdir(original_directory)
