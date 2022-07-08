from enum import Enum
import os
from typing import List, Sequence

from dagster_buildkite.utils import is_release_branch, safe_getenv

class AvailablePlatform(str, Enum):

    UNIX = "unix"
    WINDOWS = "windows"

    @classmethod
    def get_all(cls) -> Sequence["AvailablePlatform"]:
        return list(cls)

    @classmethod
    def get_default(cls) -> "AvailablePlatform":
        return cls["UNIX"]

    @classmethod
    def get_pytest_defaults(cls) -> Sequence["AvailablePlatform"]:

        branch_name = safe_getenv("BUILDKITE_BRANCH")
        commit_message = safe_getenv("BUILDKITE_MESSAGE")
        if branch_name == "master" or is_release_branch(branch_name):
            return cls.get_all()
        else:

            # environment variable-specified defaults
            # branch name or commit message-specified defaults
            test_platforms = os.environ.get("TEST_PYTHON_VERSIONS", "")

            env_vars = [branch_name, commit_message, test_platforms]

            specified_platforms: List[AvailablePlatform] = []
            for platform in cls.get_all():
                marker = f"test-{platform}"
                if any(marker in v for v in env_vars):
                    specified_platforms.append(platform)
            if any("test-all" in v or "test-all-platforms" in v for v in env_vars):
                specified_platforms += cls.get_all()

            return (
                list(set(specified_platforms))
                if len(specified_platforms) > 0
                else [cls.get_default()]
            )
