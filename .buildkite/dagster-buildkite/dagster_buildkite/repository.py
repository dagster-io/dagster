import logging
from pathlib import Path
from typing import Set

from dagster_buildkite.git import ChangedFiles
from dagster_buildkite.python_packages import PythonPackages


class Repositories:
    all: Set[Path] = set()

    @classmethod
    def load_repository(cls, git_repository_directory: Path = Path(".")) -> None:
        # Memoize
        if git_repository_directory in cls.all:
            return None

        logging.info(f"Parsing repo {git_repository_directory.absolute()}")

        ChangedFiles.load_repository(git_repository_directory)
        PythonPackages.load_repository(git_repository_directory)

        cls.all.add(git_repository_directory)
