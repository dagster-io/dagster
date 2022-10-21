import logging
import os
import subprocess
from pathlib import Path
from typing import Set

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=os.getenv("LOGLEVEL", "INFO"),
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_commit(rev):
    return subprocess.check_output(["git", "rev-parse", "--short", rev]).decode("utf-8").strip()


class ChangedFiles:
    _repositories: Set[Path] = set()
    all: Set[Path] = set()

    @classmethod
    def load_repository(cls, git_repository_directory: Path) -> None:
        # Only do the expensive git diffing once
        if git_repository_directory in cls._repositories:
            return None

        original_directory = os.getcwd()
        os.chdir(git_repository_directory)

        # TODO: Make it possible to compare to BUILDKITE_PULL_REQUEST_BASE_BRANCH
        subprocess.call(["git", "fetch", "origin", "master"])
        origin = get_commit("origin/master")
        head = get_commit("HEAD")
        logging.info(f"Changed files between origin/master ({origin}) and HEAD ({head}):")
        paths = (
            subprocess.check_output(["git", "diff", "origin/master...HEAD", "--name-only"])
            .decode("utf-8")
            .strip()
            .split("\n")
        )
        for path in paths:
            logging.info("  - " + path)
            cls.all.add(git_repository_directory / path)

        os.chdir(original_directory)
